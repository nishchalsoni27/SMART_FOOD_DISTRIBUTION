"""SQLite database layer (replaces MongoDB). The DB file is created automatically."""
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.getenv("SMARTFOOD_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "smartfood.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'donor',
    phone TEXT,
    address TEXT,
    lat REAL,
    lng REAL,
    trust_level INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    provider_name TEXT,
    food_type TEXT NOT NULL CHECK (food_type IN ('veg','non-veg')),
    quantity_kg REAL NOT NULL,
    prep_time TEXT,
    safe_until_time TEXT,
    address TEXT,
    lat REAL,
    lng REAL,
    status TEXT NOT NULL DEFAULT 'listed'
        CHECK (status IN ('listed','accepted','picked_up','delivered','expired')),
    accepted_by INTEGER,
    accepted_by_name TEXT,
    volunteer_id INTEGER,
    is_community INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ngo_id INTEGER NOT NULL,
    ngo_name TEXT,
    event_name TEXT NOT NULL,
    quantity_kg REAL NOT NULL,
    event_date TEXT,
    deadline TEXT,
    address TEXT,
    lat REAL,
    lng REAL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commitments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL REFERENCES requests(id),
    provider_id INTEGER NOT NULL,
    provider_name TEXT,
    kg REAL NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS impacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    kg_rescued REAL NOT NULL,
    meals INTEGER NOT NULL,
    co2e REAL NOT NULL,
    provider_name TEXT,
    ngo_name TEXT,
    created_at TEXT NOT NULL
);
"""


def init_db(path=None):
    with get_conn(path) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_conn(path=None):
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(path or DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
