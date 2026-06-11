from datetime import datetime, timedelta
from typing import Optional

from pymongo import MongoClient
from pymongo.synchronous.collection import Collection
from pymongo.synchronous.database import Database

from config import Config

client: MongoClient = MongoClient(Config.MONGO_URI)
db: Database = client.get_database(Config.MONGO_DB)

UID_map_collection: Collection = db.get_collection(Config.MONGO_UID_MAP)


def get_user(user_id: str) -> Optional[dict]:
    """
    Get the user details from the database
    :param user_id: The user's MyAnimeList ID
    :return: The user details
    """
    user_data = UID_map_collection.find_one({"uid": user_id})
    if user_data:
        return user_data
    return None


def store_user(user_details: dict) -> bool:
    """
    Store user details in db
    :param user_details: The user details to store
    """
    user_id = user_details["id"]
    user_details["uid"] = user_id
    data = user_details.copy()

    if user := UID_map_collection.find_one({"uid": user_id}):
        return UID_map_collection.update_one(user, {"$set": data}).acknowledged
    return UID_map_collection.insert_one(data).acknowledged


def get_valid_user(
    user_id: str,
) -> tuple[dict, Optional[str]]:
    """
    Verify the access token for the user 'user_id' from the database
    :param user_id: The user's MyAnimeList ID
    :return: A tuple of the user details if valid, and an error message if invalid
    """
    user = get_user(user_id)
    if not user:
        return {}, "No user found. Please re-login to MyAnimeList."

    if (
        not user.get("last_updated")
        or not user.get("expires_in")
        or not user.get("access_token")
        or not user.get("refresh_token")
    ):
        return {}, "Invalid MAL session. Please refresh or login again."

    expiration_date = user["last_updated"] + timedelta(seconds=user["expires_in"])
    if datetime.utcnow() > expiration_date:
        return {}, "MAL session expired. Please refresh or login again."
    return user, None
