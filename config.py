import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuration class
    """
    JSON_SORT_KEYS = False
    FLASK_HOST = os.getenv('FLASK_RUN_HOST')
    FLASK_PORT = os.getenv('FLASK_RUN_PORT')

    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DB = os.getenv('MONGO_DB')
    MONGO_ANIME_MAP = os.getenv('MONGO_ANIME_MAP_COLLECTION')