import datetime
from unittest import result
from unittest.mock import MagicMock, patch
import pytest

from app.services.db import (
    get_kitsu_id_from_mal_id,
    get_mal_id_from_kitsu_id,
    get_user,
    get_valid_user,
    store_user,
)


@patch("app.services.db.UID_map_collection.find_one")
@patch("app.services.db.UID_map_collection.insert_one")
def test_store_new_user(mock_db_insert, mock_db_find):
    """Test store_user"""
    mock_db_insert.return_value.acknowledged = True
    mock_db_find.return_value = None

    result = store_user({"id": "123", "uid": "123"})
    mock_db_insert.assert_called_once()
    mock_db_find.assert_called_once()
    assert result is True


@patch("app.services.db.UID_map_collection.find_one")
@patch("app.services.db.UID_map_collection.update_one")
def test_update_user(mock_db_update, mock_db_find):
    """Test store_user"""
    mock_db_update.return_value.acknowledged = True
    mock_db_find.return_value = {"id": "123", "uid": "123"}
    result = store_user({"id": "123", "uid": "123", "access_token": "123"})
    mock_db_update.assert_called_once()
    mock_db_find.assert_called_once()
    assert result is True


@patch("app.services.db.UID_map_collection.find_one")
def test_get_user(mock_get_user):
    """Test get_user"""
    mock_get_user.return_value = None
    user = get_user("123")
    assert user is None

    mock_get_user.return_value = {"uid": "123"}
    user = get_user("123")
    assert user == {"uid": "123"}

    mock_get_user.return_value = {"uid": "123", "access_token": "123"}
    user = get_user("123")
    assert user == {"uid": "123", "access_token": "123"}

    mock_get_user.return_value = {
        "uid": "123",
        "access_token": "123",
        "track_unlisted_anime": True,
    }
    user = get_user("123")
    assert user == {"uid": "123", "access_token": "123", "track_unlisted_anime": True}


@patch("app.services.db.get_user")
def test_valid_user(mock_get_user):
    """Test get_valid_user"""
    time = datetime.datetime.utcnow()
    mock_get_user.return_value = {
        "uid": "123",
        "access_token": "123",
        "refresh_token": "123",
        "expires_in": 3600,
        "last_updated": time,
    }
    user, error = get_valid_user("123")
    assert error is None
    assert user is not None


@patch("app.services.db.get_user")
def test_invalid_user(mock_get_user):
    """Test get_valid_user"""
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


@patch("app.services.db.anime_mapping.find_one")
def test_get_kitsu_id_from_mal_id(mock_mapping):
    """Test get_kitsu_id_from_mal_id"""
    mock_mapping.return_value = {}
    exists, kitsu_id = get_kitsu_id_from_mal_id("123")
    assert exists is False
    assert kitsu_id is ""

    mock_mapping.return_value = {"kitsu_id": "14", "mal_id": "123"}
    exists, kitsu_id = get_kitsu_id_from_mal_id("123")
    assert exists is True
    assert kitsu_id == "14"


@patch("app.services.db.anime_mapping.find_one")
def test_get_mal_id_from_kitsu_id(mock_mapping):
    """Test get_mal_id_from_kitsu_id"""
    mock_mapping.return_value = {}
    exists, mal_id = get_mal_id_from_kitsu_id("123")
    assert exists is False
    assert mal_id is ""

    mock_mapping.return_value = {"kitsu_id": "14", "mal_id": "123"}
    exists, mal_id = get_mal_id_from_kitsu_id("14")
    assert exists is True
    assert mal_id == "123"
