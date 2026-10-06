"""Smoke test of the whole demo flow (no UI needed).  Run:  python test_app.py"""
import os
import tempfile

os.environ["SMARTFOOD_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

import services as s  # noqa: E402  (must come after the env var)


def expect_error(fn, msg):
    try:
        fn()
    except s.ServiceError as e:
        assert msg in str(e), f"expected '{msg}' in '{e}'"
    else:
        raise AssertionError(f"expected error containing '{msg}'")


prov = s.register("Cafe", "p@x.com", "pw1234", "provider", address="MG Road")
ngo = s.register("Helpers", "n@x.com", "pw1234", "ngo")
other = s.register("Other NGO", "o@x.com", "pw1234", "ngo")

expect_error(lambda: s.register("d", "p@x.com", "pw1234"), "already registered")
expect_error(lambda: s.login("p@x.com", "bad-pass"), "Wrong password")
expect_error(lambda: s.login("nobody@x.com", "pw"), "User not found")
assert s.login("p@x.com", "pw1234")["role"] == "provider"
assert s.predict_surplus() == 5.0

expect_error(lambda: s.create_listing(prov, "meat", 5), "Food type")
lid = s.create_listing(prov, "veg", 8, safe_hours=4)
assert s.list_listings(status="listed")[0]["status"] == "listed"

s.accept_listing(lid, ngo)
expect_error(lambda: s.accept_listing(lid, other), "Already taken")  # atomic accept
assert s.list_listings(status="listed") == []
assert s.list_listings(accepted_by=ngo["id"])[0]["accepted_by_name"] == "Helpers"

expect_error(lambda: s.update_status(lid, "delivered", other), "Only the NGO")
s.update_status(lid, "picked_up", ngo)
s.update_status(lid, "delivered", ngo)
expect_error(lambda: s.update_status(lid, "delivered", ngo), "Already delivered")  # no double impact

d = s.impact_summary()
assert (d["meals"], d["kg"], d["co2e"], d["count"]) == (20, 8.0, 20.0, 1), d
assert s.predict_surplus() == 8.0

s.create_request(ngo, "Fest", 30)
rid = s.list_requests()[0]["id"]
s.commit_to_request(rid, prov, 5)
r = s.list_requests()[0]
assert r["commitments"][0]["kg"] == 5 and len(s.list_requests()) == 1
print("All checks passed")
