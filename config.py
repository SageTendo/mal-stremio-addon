import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuration class
    """
    JSON_SORT_KEYS = False
    FLASK_HOST = os.getenv('FLASK_RUN_HOST', "localhost")
    FLASK_PORT = os.getenv('FLASK_RUN_PORT', "5000")
    SECRET_KEY = os.getenv('SECRET_KEY', "this is not a secret key")
    SESSION_TYPE = os.getenv('SESSION_TYPE', "filesystem")
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    DEBUG = os.getenv('FLASK_DEBUG', False)

    # MongoDB
    MONGO_URI = os.getenv('MONGO_URI', "")
    MONGO_DB = os.getenv('MONGO_DB', "")
    MONGO_UID_MAP = os.getenv('MONGO_UID_MAP_COLLECTION', "")

    # Env dependent configs
    if DEBUG in ["1", True, "True"]:  # Local development
        PROTOCOL = "http"
        REDIRECT_URL = f"{FLASK_HOST}:{FLASK_PORT}"
    else:  # Production environment
        PROTOCOL = "https"
        REDIRECT_URL = f"{FLASK_HOST}"
