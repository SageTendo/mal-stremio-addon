from pymongo import MongoClient

from config import Config

client = MongoClient(Config.MONGO_URI)
db = client.get_database(Config.MONGO_DB)
anime_map_collection = db.get_collection(Config.MONGO_ANIME_MAP)
