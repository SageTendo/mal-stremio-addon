import re
from functools import lru_cache
from typing import Dict, Tuple

from pymongo import MongoClient

from app.routes.utils import log_error
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client.get_database(Config.MONGO_DB)
anime_db = client.get_database(Config.MONGO_ANIME_DB)

UID_map_collection = db.get_collection(Config.MONGO_UID_MAP)
anime_mapping = anime_db.get_collection(Config.MONGO_ANIME_MAP)


def store_user(user_details: Dict):
    """
    Store user details in db
    :param user_details: The user details to store
    """
    user_id = user_details['id']
    access_token = user_details['access_token']
    refresh_tkn = user_details['refresh_token']
    expires_in = user_details['expires_in']

    user = UID_map_collection.find_one({'uid': user_id})
    if user:
        result = UID_map_collection.update_one(user, {'$set': {'access_token': access_token,
                                                               'refresh_token': refresh_tkn,
                                                               'expires_in': expires_in}})
    else:
        result = UID_map_collection.insert_one(
            {'uid': user_id, 'access_token': access_token, 'refresh_token': refresh_tkn, 'expires_in': expires_in})
    return result.acknowledged


@lru_cache(maxsize=10000)
def get_kitsu_id_from_mal_id(mal_id) -> Tuple[bool, str]:
    """
    Get kitsu_id from mal_id from db
    :param mal_id: The MyAnimeList id of the anime
    :return: A tuple of (found, kitsu_id)
    """
    mal_id = re.sub(r'[^0-9]', '', str(mal_id))
    try:
        mal_id = int(mal_id)
        if res := anime_mapping.find_one({'mal_id': mal_id}):
            if not res.get('kitsu_id', None):
                return False, ''
            return True, res['kitsu_id']
    except KeyError:
        log_error(f"No Kitsu ID for: MAL:{mal_id}")
    except ValueError:
        log_error(f"Invalid MyAnimeList ID: {mal_id}")
    return False, ''


@lru_cache(maxsize=10000)
def get_mal_id_from_kitsu_id(kitsu_id) -> Tuple[bool, str]:
    """
    Get mal_id from kitsu_id from db
    :param kitsu_id: The kitsu id of the anime
    :return: A tuple of (found, mal_id)
    """
    kitsu_id = re.sub(r'[^0-9]', '', str(kitsu_id))
    try:
        kitsu_id = int(kitsu_id)
        res = anime_mapping.find_one({'kitsu_id': kitsu_id})
        if res:
            if not res.get('mal_id', None):
                return False, ''
            return True, res['mal_id']
    except KeyError:
        log_error(f"No MAL ID for KITSU:{kitsu_id}")
    except ValueError:
        log_error(f"Invalid kitsu ID: {kitsu_id}")
    return False, ''
