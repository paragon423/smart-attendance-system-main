#!/usr/bin/env python3
"""SmartTime demo web server with SQLite persistence (Python standard library only)."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
import math
import sqlite3
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "smarttime.sqlite3"
HOST = "0.0.0.0"
PORT = 8000

DEFAULT_STATE = {
    "users": [
        {"id": "admin", "empId": "MADA-001", "name": "Admin User", "email": "admin@mada.example", "role": "Administrator", "active": True},
        {"id": "staff1", "empId": "MADA-002", "name": "Amina Yusuf", "email": "amina@mada.example", "role": "Employee", "active": True},
        {"id": "staff2", "empId": "MADA-003", "name": "Musa Bello", "email": "musa@mada.example", "role": "Employee", "active": True},
        {"id": "manager", "empId": "MADA-004", "name": "Team Manager", "email": "manager@mada.example", "role": "Manager", "active": True},
    ],
    "records": [],
    "settings": {"workName": "MADA Multi-Links Head Office", "lat": "", "lon": "", "radius": 150, "start": "09:00", "grace": 10, "qr": "MADA-SMARTTIME-DEMO"},
}


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_connection():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize():
    with db_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, emp_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
                email TEXT NOT NULL, role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                employee TEXT NOT NULL, emp_id TEXT NOT NULL, work_date TEXT NOT NULL,
                check_in TEXT NOT NULL DEFAULT '', check_out TEXT NOT NULL DEFAULT '',
                method TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT '',
                verified TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            );
        """)
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            _write_state(conn, DEFAULT_STATE)


def _write_state(conn, state):
    users = state.get("users")
    records = state.get("records")
    settings = state.get("settings")
    if not isinstance(users, list) or not isinstance(records, list) or not isinstance(settings, dict):
        raise ValueError("Expected users and records arrays and a settings object")
    # Validate essential fields before replacing any saved data.
    seen_ids, seen_emp_ids = set(), set()
    for user in users:
        if not isinstance(user, dict) or not all(str(user.get(k, "")).strip() for k in ("id", "empId", "name", "email", "role")):
            raise ValueError("Every user must have id, empId, name, email and role")
        if user["id"] in seen_ids or user["empId"].lower() in seen_emp_ids:
            raise ValueError("Duplicate user ID or employee ID")
        seen_ids.add(user["id"])
        seen_emp_ids.add(user["empId"].lower())
    lat, lon = settings.get("lat", ""), settings.get("lon", "")
    if str(lat).strip() and str(lon).strip():
        try:
            if not math.isfinite(float(lat)) or not math.isfinite(float(lon)) or abs(float(lat)) > 90 or abs(float(lon)) > 180:
                raise ValueError("Invalid workplace coordinates")
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid workplace coordinates") from exc

    conn.execute("DELETE FROM attendance")
    conn.execute("DELETE FROM users")
    for user in users:
        conn.execute("INSERT INTO users(id,emp_id,name,email,role,active) VALUES(?,?,?,?,?,?)", (
            str(user["id"]), str(user["empId"]), str(user["name"]), str(user["email"]),
            str(user["role"]), 1 if user.get("active", True) else 0))
    for record in records:
        if not isinstance(record, dict):
            continue
        user_id = str(record.get("userId", ""))
        if user_id not in seen_ids:
            continue
        conn.execute("""INSERT INTO attendance(user_id,employee,emp_id,work_date,check_in,check_out,method,status,verified)
                        VALUES(?,?,?,?,?,?,?,?,?)""", (
            user_id, str(record.get("employee", "")), str(record.get("empId", "")),
            str(record.get("date", "")), str(record.get("checkIn", "")), str(record.get("checkOut", "")),
            str(record.get("method", "")), str(record.get("status", "")), str(record.get("verified", ""))))
    conn.execute("DELETE FROM settings")
    for key, value in settings.items():
        conn.execute("INSERT INTO settings(key,value) VALUES(?,?)", (str(key), json.dumps(value)))


def read_state():
    with db_connection() as conn:
        users = [{"id": r["id"], "empId": r["emp_id"], "name": r["name"], "email": r["email"], "role": r["role"], "active": bool(r["active"])}
                 for r in conn.execute("SELECT * FROM users ORDER BY rowid")]
        records = [{"userId": r["user_id"], "employee": r["employee"], "empId": r["emp_id"], "date": r["work_date"],
                    "checkIn": r["check_in"], "checkOut": r["check_out"], "method": r["method"], "status": r["status"], "verified": r["verified"]}
                   for r in conn.execute("SELECT * FROM attendance ORDER BY id DESC")]
        settings = {r["key"]: json.loads(r["value"]) for r in conn.execute("SELECT * FROM settings")}
    # Keep the expected keys available if a settings entry is missing.
    merged_settings = dict(DEFAULT_STATE["settings"])
    merged_settings.update(settings)
    return {"users": users, "records": records, "settings": merged_settings}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def _json(self, status, data):
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/db":
            try:
                self._json(200, read_state())
            except Exception as exc:
                self._json(500, {"error": "Could not read SQLite database", "detail": str(exc)})
            return
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/db":
            self._json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 5_000_000:
                self._json(413, {"error": "Invalid request size"})
                return
            state = json.loads(self.rfile.read(length).decode("utf-8"))
            with db_connection() as conn:
                _write_state(conn, state)
            self._json(200, {"ok": True})
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": "Could not save SQLite database", "detail": str(exc)})

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


if __name__ == "__main__":
    initialize()
    print(f"SmartTime running at http://localhost:{PORT}/")
    print(f"SQLite database: {DB_PATH}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
