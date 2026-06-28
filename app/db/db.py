from app.db import DBBackend
from app.db.mongo import _MongoBackend
from app.db.sqlite import _SQLiteBackend
from config import Config


def _make_backend() -> DBBackend:
    if Config.DB_BACKEND == "mongo":
        return _MongoBackend()
    return _SQLiteBackend()


db_backend = _make_backend()
