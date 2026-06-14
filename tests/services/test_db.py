import datetime
from unittest.mock import patch

import mongomock
import pytest

from app.db.mongo import _MongoBackend
from app.db.sqlite import _SQLiteBackend
from app.services.db import get_user, get_valid_user, store_user
from config import Config


# ── Backend fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def sqlite_backend(tmp_path):
    with patch.object(Config, "SQLITE_PATH", str(tmp_path / "test.db")):
        yield _SQLiteBackend()


@pytest.fixture
def mongo_backend():
    with patch("pymongo.MongoClient", mongomock.MongoClient), \
         patch.object(Config, "MONGO_URI", "mongodb://localhost/"), \
         patch.object(Config, "MONGO_DB", "testdb"), \
         patch.object(Config, "MONGO_UID_MAP", "users"):
        yield _MongoBackend()


@pytest.fixture(params=["sqlite", "mongo"])
def backend(request, sqlite_backend, mongo_backend):
    return sqlite_backend if request.param == "sqlite" else mongo_backend


# ── Backend-level tests (run against both SQLite and Mongo) ───────────────────

def test_backend_store_new_user(backend):
    assert backend.store_user({"id": "123"}) is True
    user = backend.get_user("123")
    assert user is not None
    assert user["uid"] == "123"


def test_backend_update_user(backend):
    backend.store_user({"id": "123"})
    assert backend.store_user({"id": "123", "access_token": "tok"}) is True
    user = backend.get_user("123")
    assert user["access_token"] == "tok"


def test_backend_get_nonexistent_user(backend):
    assert backend.get_user("nonexistent") is None


# ── Service-layer tests (mock db_backend) ─────────────────────────────────────

@patch("app.services.db.db_backend")
def test_store_new_user(mock_backend):
    mock_backend.store_user.return_value = True
    result = store_user({"id": "123", "uid": "123"})
    mock_backend.store_user.assert_called_once_with({"id": "123", "uid": "123"})
    assert result is True


@patch("app.services.db.db_backend")
def test_get_user(mock_backend):
    mock_backend.get_user.return_value = None
    assert get_user("123") is None

    mock_backend.get_user.return_value = {"uid": "123"}
    assert get_user("123") == {"uid": "123"}

    mock_backend.get_user.return_value = {"uid": "123", "access_token": "abc"}
    assert get_user("123") == {"uid": "123", "access_token": "abc"}

    mock_backend.get_user.return_value = {
        "uid": "123",
        "access_token": "abc",
        "track_unlisted_anime": True,
    }
    assert get_user("123") == {
        "uid": "123",
        "access_token": "abc",
        "track_unlisted_anime": True,
    }


@patch("app.services.db.get_user")
def test_valid_user(mock_get_user):
    now = datetime.datetime.utcnow()
    mock_get_user.return_value = {
        "uid": "123",
        "access_token": "123",
        "refresh_token": "123",
        "expires_in": 3600,
        "last_updated": now,
    }
    user, error = get_valid_user("123")
    assert error is None
    assert user is not None


@patch("app.services.db.get_user")
def test_invalid_user(mock_get_user):
    mock_get_user.return_value = None
    user, error = get_valid_user("123")
    assert error == "No user found. Please re-login to MyAnimeList."
    assert not user


@patch("app.services.db.get_user")
def test_invalid_mal_session(mock_get_user):
    mock_get_user.return_value = {
        "uid": "123",
        "access_token": "123",
        "refresh_token": "123",
        "expires_in": 3600,
    }
    user, error = get_valid_user("123")
    assert error == "Invalid MAL session. Please refresh or login again."
    assert not user


@patch("app.services.db.get_user")
def test_invalid_mal_session_expired(mock_get_user):
    mock_get_user.return_value = {
        "uid": "123",
        "access_token": "123",
        "refresh_token": "123",
        "expires_in": 3600,
        "last_updated": datetime.datetime.utcnow() - datetime.timedelta(seconds=3601),
    }
    user, error = get_valid_user("123")
    assert error == "MAL session expired. Please refresh or login again."
    assert not user
