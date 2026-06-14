from typing import Optional

from app.db import DBBackend
from config import Config


class _MongoBackend(DBBackend):
    def __init__(self):
        from pymongo import ASCENDING, MongoClient

        client = MongoClient(Config.MONGO_URI)
        db = client.get_database(Config.MONGO_DB)
        self._col = db.get_collection(Config.MONGO_UID_MAP)
        self._col.create_index([("uid", ASCENDING)], unique=True)

    def get_user(self, user_id: str) -> Optional[dict]:
        return self._col.find_one({"uid": user_id})

    def store_user(self, user_details: dict) -> bool:
        user_id = user_details["id"]
        data = user_details.copy()
        data["uid"] = user_id

        if user := self._col.find_one({"uid": user_id}):
            return self._col.update_one(user, {"$set": data}).acknowledged
        return self._col.insert_one(data).acknowledged
