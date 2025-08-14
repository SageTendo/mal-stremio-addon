import re
from functools import lru_cache
from typing import Dict, Tuple

from pymongo import MongoClient

import config
from app.routes.utils import log_error
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client.get_database(Config.MONGO_DB)
anime_db = client.get_database(Config.MONGO_ANIME_DB)

UID_map_collection = db.get_collection(Config.MONGO_UID_MAP)
anime_mapping = anime_db.get_collection(Config.MONGO_ANIME_MAP)


def get_user(user_id: str):
    """
    Get the user details from the database
    :param user_id: The user's MyAnimeList ID
    :return: The user details
    """
    return UID_map_collection.find_one({"uid": user_id})


def store_user(user_details: dict):
    """
    Store user details in db
    :param user_details: The user details to store
    """
    user_id = user_details["id"]
    user_details["uid"] = user_id
    data = user_details.copy()

    if user := UID_map_collection.find_one({"uid": user_id}):
        result = UID_map_collection.update_one(user, {"$set": data})
    else:
        result = UID_map_collection.insert_one(data)
    return result.acknowledged


@lru_cache(maxsize=config.ID_CACHE_SIZE)
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


@lru_cache(maxsize=config.ID_CACHE_SIZE)
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
