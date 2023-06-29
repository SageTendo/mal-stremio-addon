import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuration class
    """
    JSON_SORT_KEYS = False
    FLASK_HOST = os.getenv('FLASK_RUN_HOST', "localhost")
    FLASK_PORT = os.getenv('FLASK_RUN_PORT', "5000")
    DEBUG = os.getenv('FLASK_DEBUG', 0)

    MONGO_URI = os.getenv('MONGO_URI', "")
    MONGO_DB = os.getenv('MONGO_DB', "")
    MONGO_ANIME_MAP = os.getenv('MONGO_ANIME_MAP_COLLECTION', "")

    # redirect URI depending on environment
    if int(DEBUG) == 1:
        # Local development
        REDIRECT_URI = f"http://{FLASK_HOST}:{FLASK_PORT}"
    else:
        # Production environment
        REDIRECT_URI = f"https://{FLASK_HOST}"
