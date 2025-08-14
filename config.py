import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuration class
    """

    JSON_SORT_KEYS = False
    FLASK_HOST = os.getenv("FLASK_RUN_HOST", "localhost")
    FLASK_PORT = os.getenv("FLASK_RUN_PORT", "5000")
    SECRET_KEY = os.getenv("SECRET_KEY", "this is not a secret key")
    SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=7)
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    COMPRESS_ALGORITHM = ["gzip"]
    COMPRESS_BR_LEVEL = 4
    DEBUG = os.getenv("FLASK_DEBUG", False)

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DB = os.getenv("MONGO_DB", "")
    MONGO_UID_MAP = os.getenv("MONGO_UID_MAP_COLLECTION", "")
    MONGO_ANIME_DB = os.getenv("MONGO_ANIME_DATABASE", "")
    MONGO_ANIME_MAP = os.getenv("MONGO_ANIME_MAP_COLLECTION", "")

    # Env dependent configs
    if DEBUG in ["1", True, "True"]:  # Local development
        PROTOCOL = "http"
        REDIRECT_URL = f"{FLASK_HOST}:{FLASK_PORT}"
    else:  # Production environment
        PROTOCOL = "https"
        REDIRECT_URL = f"{FLASK_HOST}"


# headers for external API requests
REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# LRU Cache sizes
META_CACHE_SIZE = 25000
ID_CACHE_SIZE = 50000
STREAM_CACHE_SIZE = 20000

# Cache durations
DEFAULT_STALE_WHILE_REVALIDATE = 600  # 10 minutes
DEFAULT_STALE_IF_ERROR = 300  # 5 minutes
MANIFEST_CACHE_DURATION = 3600  # 1 hour
CATALOG_CACHE_ON_SUCCESS_DURATION = 900  # 15 minutes
CATALOG_CACHE_STALE_WHILE_REVALIDATE = 300  # 5 minutes
CATALOG_STALE_IF_ERROR = 86400  # 1 day
META_CACHE_ON_SUCCESS_DURATION = 86400 * 30  # 30 days
META_CACHE_ON_INVALID_DURATION = 86400 * 365  # 1 year
STREAM_CACHE_ON_SUCCESS_DURATION = 3600 * 3  # 3 hours
STREAM_CACHE_ON_FAIL_TO_FETCH_DURATION = 3600  # 1 hour
STREAM_CACHE_ON_INVALID_DURATION = 86400 * 365  # 1 year
STREAM_CACHE_ON_NO_KITSU_ID_DURATION = 86400  # 1 day
STREAM_CACHE_STALE_WHILE_REVALIDATE = 5  # 5 seconds
CONTENT_SYNC_NO_UPDATE_DURATION = 86400  # 1 day
CONTENT_SYNC_CACHE_ON_INVALID_DURATION = 86400 * 365  # 1 year

# Addon configuration options
DEFAULT_SORT_OPTION = "list_updated_at"
SORT_OPTIONS = {
    "Last Updated": "list_updated_at",
    "Title": "anime_title",
    "Release Date": "anime_start_date",
    "Score": "list_score",
}
