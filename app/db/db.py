from pymongo import MongoClient

from . import MONGO_URI, MONGO_DB, MONGO_COLLECTION

client = MongoClient(MONGO_URI)
map_db = client[MONGO_DB][MONGO_COLLECTION]

if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()

    mongo_uri = os.environ.get('MONGO_URI')
    mongo_db = os.environ.get('MONGO_DB')
    mongo_collection = os.environ.get('MONGO_COLLECTION')
    client = MongoClient()
    map_db = client[mongo_db][mongo_collection]
    print(map_db.find_one({'mal_id': 2981}))
