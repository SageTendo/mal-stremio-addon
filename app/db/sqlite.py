import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from app.db import DBBackend
from config import Config


class _SQLiteBackend(DBBackend):
    _CREATE_CACHE_TABLE = """
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    """

    _COLS = (
        "uid",
        "access_token",
        "refresh_token",
        "expires_in",
        "last_updated",
        "catalogs",
        "sort_watchlist",
        "track_unlisted_anime",
        "nsfw_enabled",
    )
    _UPSERT_USER = (
        "INSERT INTO users ({cols}) VALUES ({placeholders}) "
        "ON CONFLICT(uid) DO UPDATE SET {updates}"
    ).format(
        cols=", ".join(_COLS),
        placeholders=", ".join("?" * len(_COLS)),
        updates=", ".join(f"{col} = excluded.{col}" for col in _COLS if col != "uid"),
    )
    _CREATE_USER_TABLE = """
        CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY,
            access_token TEXT,
            refresh_token TEXT,
            expires_in INTEGER,
            last_updated TEXT,
            catalogs TEXT,
            sort_watchlist TEXT,
            track_unlisted_anime INTEGER,
            nsfw_enabled INTEGER
        )
    """

    def __init__(self):
        self._path = Config.SQLITE_PATH
        with self._connect() as con:
            con.execute(self._CREATE_USER_TABLE)
            con.execute(self._CREATE_CACHE_TABLE)

    def _connect(self):
        con = sqlite3.connect(self._path)
        con.row_factory = sqlite3.Row
        return con

    def _deserialize_user(self, row: sqlite3.Row) -> dict:
        data = dict(row)
        if data.get("catalogs"):
            data["catalogs"] = json.loads(data["catalogs"])

        if data.get("last_updated"):
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])

        data["track_unlisted_anime"] = bool(data.get("track_unlisted_anime"))
        data["nsfw_enabled"] = bool(data.get("nsfw_enabled"))
        return data

    def get_user(self, user_id: str) -> Optional[dict]:
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM users WHERE uid = ?", (user_id,)
            ).fetchone()
        return self._deserialize_user(row) if row else None

    def store_user(self, user_details: dict) -> bool:
        data = user_details.copy()
        data["uid"] = data.pop("id", data.get("uid"))

        if isinstance(data.get("catalogs"), list):
            data["catalogs"] = json.dumps(data["catalogs"])
        if isinstance(data.get("last_updated"), datetime):
            data["last_updated"] = data["last_updated"].isoformat()

        values = [data.get(col) for col in self._COLS]
        try:
            with self._connect() as con:
                con.execute(self._UPSERT_USER, values)
            return True
        except sqlite3.Error:
            return False

    def get_cache(self, key: str) -> Optional[dict]:
        with self._connect() as con:
            row = con.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            ).fetchone()

        if not row:
            return None
        if datetime.utcnow() > datetime.fromisoformat(row["expires_at"]):
            return None
        return json.loads(row["value"])

    def set_cache(self, key: str, value: dict, ttl_seconds: int) -> bool:
        expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()
        try:
            with self._connect() as con:
                con.execute(
                    "INSERT INTO cache (key, value, expires_at) VALUES (?, ?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
                    "expires_at = excluded.expires_at",
                    (key, json.dumps(value), expires_at),
                )
            return True
        except sqlite3.Error:
            return False
