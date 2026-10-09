"""All business logic (auth, listings, event requests, impact). No UI code here."""
import hashlib
import hmac
import os
import re
from datetime import datetime, timedelta, timezone

from db import get_conn, init_db

ROLES = ("provider", "ngo", "volunteer", "donor")
FOOD_TYPES = ("veg", "non-veg")
STATUSES = ("listed", "accepted", "picked_up", "delivered", "expired")
DEFAULT_LAT, DEFAULT_LNG = 23.2599, 77.4126  # demo coordinates (same as the original app)
KG_PER_MEAL = 0.4
CO2E_PER_KG = 2.5


class ServiceError(Exception):
    """Raised for user-facing problems (bad input, wrong password, already taken...)."""


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def in_hours(hours):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat(timespec="seconds")


def fmt_time(iso):
    """ISO UTC string -> readable local time."""
    if not iso:
        return "-"
    return datetime.fromisoformat(iso).astimezone().strftime("%d %b %H:%M")


# ---------------------------------------------------------------- auth
def _hash(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + "$" + digest.hex()


def _verify(password, stored):
    salt_hex, digest_hex = stored.split("$")
    test = _hash(password, bytes.fromhex(salt_hex)).split("$")[1]
    return hmac.compare_digest(test, digest_hex)


def _user_dict(row):
    return {
        "id": row["id"], "name": row["name"], "email": row["email"], "role": row["role"],
        "phone": row["phone"], "address": row["address"], "lat": row["lat"], "lng": row["lng"],
    }


def register(name, email, password, role="donor", phone="", address=""):
    name, email = (name or "").strip(), (email or "").strip().lower()
    if not name:
        raise ServiceError("Name is required")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ServiceError("Enter a valid email")
    if len(password or "") < 4:
        raise ServiceError("Password must be at least 4 characters")
    if role not in ROLES:
        raise ServiceError(f"Invalid role: {role}")
    with get_conn() as c:
        if c.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            raise ServiceError("Email already registered")
        cur = c.execute(
            "INSERT INTO users (name,email,password_hash,role,phone,address,lat,lng,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (name, email, _hash(password), role, phone, address, DEFAULT_LAT, DEFAULT_LNG, now_iso()),
        )
        row = c.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
    return _user_dict(row)


def login(email, password):
    with get_conn() as c:
        row = c.execute("SELECT * FROM users WHERE email=?", ((email or "").strip().lower(),)).fetchone()
    if not row:
        raise ServiceError("User Email not found")
    if not _verify(password or "", row["password_hash"]):
        raise ServiceError("Wrong password")
    return _user_dict(row)


# ---------------------------------------------------------------- listings
def create_listing(user, food_type, quantity_kg, safe_hours=4, address="", is_community=False):
    if food_type not in FOOD_TYPES:
        raise ServiceError("Food type must be 'veg' or 'non-veg'")
    if not quantity_kg or quantity_kg <= 0:
        raise ServiceError("Quantity must be greater than 0")
    ts = now_iso()
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO listings (provider_id,provider_name,food_type,quantity_kg,prep_time,"
            "safe_until_time,address,lat,lng,is_community,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (user["id"], user["name"], food_type, float(quantity_kg), ts, in_hours(safe_hours),
             address or user.get("address") or "", user.get("lat") or DEFAULT_LAT,
             user.get("lng") or DEFAULT_LNG, int(is_community), ts, ts),
        )
        return cur.lastrowid


def list_listings(status=None, provider_id=None, accepted_by=None):
    sql, args = "SELECT * FROM listings WHERE 1=1", []
    for col, val in (("status", status), ("provider_id", provider_id), ("accepted_by", accepted_by)):
        if val is not None:
            sql += f" AND {col}=?"
            args.append(val)
    with get_conn() as c:
        return [dict(r) for r in c.execute(sql + " ORDER BY created_at DESC, id DESC", args)]


def accept_listing(listing_id, user):
    """Atomic accept: the UPDATE only matches while the listing is still 'listed'."""
    with get_conn() as c:
        cur = c.execute(
            "UPDATE listings SET status='accepted', accepted_by=?, accepted_by_name=?, updated_at=? "
            "WHERE id=? AND status='listed'",
            (user["id"], user["name"], now_iso(), listing_id),
        )
        if cur.rowcount == 0:
            raise ServiceError("Already taken by another NGO")


def update_status(listing_id, status, user):
    if status not in STATUSES:
        raise ServiceError("Invalid status")
    with get_conn() as c:
        listing = c.execute("SELECT * FROM listings WHERE id=?", (listing_id,)).fetchone()
        if not listing:
            raise ServiceError("Listing not found")
        if listing["accepted_by"] != user["id"]:
            raise ServiceError("Only the NGO that accepted this listing can update it")
        if listing["status"] == "delivered":
            raise ServiceError("Already delivered")
        c.execute("UPDATE listings SET status=?, updated_at=? WHERE id=?", (status, now_iso(), listing_id))
        if status == "delivered":
            kg = listing["quantity_kg"] or 0
            c.execute(
                "INSERT INTO impacts (listing_id,kg_rescued,meals,co2e,provider_name,ngo_name,created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (listing_id, kg, round(kg / KG_PER_MEAL), round(kg * CO2E_PER_KG, 2),
                 listing["provider_name"], listing["accepted_by_name"], now_iso()),
            )


# ---------------------------------------------------------------- event requests
def create_request(user, event_name, quantity_kg, address=""):
    if not (event_name or "").strip():
        raise ServiceError("Event name is required")
    if not quantity_kg or quantity_kg <= 0:
        raise ServiceError("Quantity must be greater than 0")
    with get_conn() as c:
        c.execute(
            "INSERT INTO requests (ngo_id,ngo_name,event_name,quantity_kg,event_date,deadline,"
            "address,lat,lng,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (user["id"], user["name"], event_name.strip(), float(quantity_kg), now_iso(), in_hours(24),
             address or user.get("address") or "", user.get("lat") or DEFAULT_LAT,
             user.get("lng") or DEFAULT_LNG, now_iso()),
        )


def list_requests():
    with get_conn() as c:
        reqs = [dict(r) for r in c.execute("SELECT * FROM requests ORDER BY created_at DESC, id DESC")]
        for r in reqs:
            r["commitments"] = [
                dict(x) for x in c.execute("SELECT * FROM commitments WHERE request_id=?", (r["id"],))
            ]
    return reqs


def commit_to_request(request_id, user, kg):
    if not kg or kg <= 0:
        raise ServiceError("Enter kg greater than 0")
    with get_conn() as c:
        if not c.execute("SELECT 1 FROM requests WHERE id=?", (request_id,)).fetchone():
            raise ServiceError("Request not found")
        c.execute(
            "INSERT INTO commitments (request_id,provider_id,provider_name,kg,created_at) VALUES (?,?,?,?,?)",
            (request_id, user["id"], user["name"], float(kg), now_iso()),
        )


# ---------------------------------------------------------------- impact
def impact_summary():
    with get_conn() as c:
        t = c.execute(
            "SELECT COALESCE(SUM(meals),0) m, COALESCE(SUM(kg_rescued),0) k, "
            "COALESCE(SUM(co2e),0) c, COUNT(*) n FROM impacts"
        ).fetchone()
        recent = [dict(r) for r in c.execute("SELECT * FROM impacts ORDER BY id DESC LIMIT 10")]
    return {"meals": int(t["m"]), "kg": float(t["k"]), "co2e": float(t["c"]), "count": t["n"], "recent": recent}


def predict_surplus(provider_id=None):
    """Rule-based predictor: average of the last 7 rescues (5 kg if there is no history)."""
    with get_conn() as c:
        rows = c.execute("SELECT kg_rescued FROM impacts ORDER BY id DESC LIMIT 7").fetchall()
    return round(sum(r["kg_rescued"] for r in rows) / len(rows), 1) if rows else 5.0


init_db()
