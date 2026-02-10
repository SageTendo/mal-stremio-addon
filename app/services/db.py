import re
from datetime import datetime, timedelta
from typing import Optional

from pymongo import MongoClient
from pymongo.synchronous.collection import Collection
from pymongo.synchronous.database import Database

from app.routes.utils import log_error
from config import Config

client: MongoClient = MongoClient(Config.MONGO_URI)
db: Database = client.get_database(Config.MONGO_DB)
anime_db: Database = client.get_database(Config.MONGO_ANIME_DB)

UID_map_collection: Collection = db.get_collection(Config.MONGO_UID_MAP)
anime_mapping: Collection = anime_db.get_collection(Config.MONGO_ANIME_MAP)


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


def get_kitsu_id_from_mal_id(mal_id) -> tuple[bool, str]:
    """
    Get kitsu_id from mal_id from db
    :param mal_id: The MyAnimeList id of the anime
    :return: A tuple of (found, kitsu_id)
    """
    mal_id = re.sub(r"[^0-9]", "", str(mal_id))
    try:
        mal_id = int(mal_id)
        if res := anime_mapping.find_one({"mal_id": mal_id}):
            if not res.get("kitsu_id", None):
                return False, ""
            return True, res["kitsu_id"]
    except KeyError:
        log_error("KEY ERROR", f"No Kitsu ID for MAL={mal_id}", "Missing mapping in DB")
    except ValueError:
        log_error("VALUE ERROR", f"Invalid MAL ID: {mal_id}", "Invalid MAL ID")
    return False, ""


def get_mal_id_from_kitsu_id(kitsu_id) -> tuple[bool, str]:
    """
    Get mal_id from kitsu_id from db
    :param kitsu_id: The kitsu id of the anime
    :return: A tuple of (found, mal_id)
    """
    kitsu_id = re.sub(r"[^0-9]", "", str(kitsu_id))
    try:
        kitsu_id = int(kitsu_id)
        res = anime_mapping.find_one({"kitsu_id": kitsu_id})
        if res:
            if not res.get("mal_id", None):
                return False, ""
            return True, res["mal_id"]
    except KeyError:
        log_error(
            "KEY ERROR", f"No MAL ID for Kitsu={kitsu_id}", "Missing mapping in DB"
        )
    except ValueError:
        log_error("VALUE ERROR", f"Invalid Kitsu ID: {kitsu_id}", "Invalid Kitsu ID")
    return False, ""


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
