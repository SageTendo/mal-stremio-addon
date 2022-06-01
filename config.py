import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    JSON_SORT_KEYS = False
    HOST = os.getenv('FLASK_RUN_HOST')
    PORT = os.getenv('FLASK_RUN_PORT')

    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DB = os.getenv('MONGO_DB')
    MONGO_COLLECTION = os.getenv('MONGO_COLLECTION')


class Prod(Config):
    DEBUG = False


class Dev(Config):
    DEBUG = True
