from pymongo import MongoClient

from config import Config

client = MongoClient(Config.MONGO_URI)
map_db = client[Config.MONGO_DB][Config.MONGO_COLLECTION]

if __name__ == '__main__':
    print(map_db.find_one({'mal_id': 2981}))
