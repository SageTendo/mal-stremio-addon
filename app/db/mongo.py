from datetime import datetime, timedelta
from typing import Optional

from app.db import DBBackend
from config import Config


class _MongoBackend(DBBackend):
    def __init__(self):
        from pymongo import ASCENDING, MongoClient

        client = MongoClient(Config.MONGO_URI)
        db = client.get_database(Config.MONGO_DB)
        self._col = db.get_collection(Config.MONGO_UID_MAP)
        self._col.create_index([("uid", ASCENDING)], unique=True, name="uid")

        self._cache_col = db.get_collection(Config.MONGO_CACHE_COLLECTION)
        self._cache_col.create_index(
            [("expires_at", ASCENDING)], expireAfterSeconds=0, name="expires_at_ttl"
        )

    def get_user(self, user_id: str) -> Optional[dict]:
        return self._col.find_one({"uid": user_id})

    def store_user(self, user_details: dict) -> bool:
        user_id = user_details["id"]
        data = user_details.copy()
        data["uid"] = user_id

        return self._col.update_one(
            {"uid": user_id}, {"$set": data}, upsert=True
        ).acknowledged

    def get_cache(self, key: str) -> Optional[dict]:
        doc = self._cache_col.find_one({"_id": key})
        return doc["value"] if doc else None

    def set_cache(self, key: str, value: dict, ttl_seconds: int) -> bool:
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        return self._cache_col.update_one(
            {"_id": key},
            {"$set": {"value": value, "expires_at": expires_at}},
            upsert=True,
        ).acknowledged
