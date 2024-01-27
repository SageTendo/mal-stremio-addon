from pymongo import MongoClient

from config import Config

client = MongoClient(Config.MONGO_URI)
db = client.get_database(Config.MONGO_DB)
anime_map_collection = db.get_collection(Config.MONGO_ANIME_MAP)
UID_map_collection = db.get_collection(Config.MONGO_UID_MAP)


def store_user(user_details):
    user_id = user_details['id']
    access_token = user_details['access_token']
    refresh_tkn = user_details['refresh_token']
    expires_in = user_details['expires_in']

    user = UID_map_collection.find_one({'uid': user_id})
    if user:
        UID_map_collection.update_one(user, {'$set': {'access_token': access_token, 'refresh_token': refresh_tkn,
                                                      'expires_in': expires_in}})
    else:
        UID_map_collection.insert_one(
            {'uid': user_id, 'access_token': access_token, 'refresh_token': refresh_tkn, 'expires_in': expires_in})
