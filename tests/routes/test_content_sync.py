import sys
from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio

from app.routes.content_sync import (
    UpdateStatus,
    determine_watch_dates,
    handle_content_id,
    handle_current_status,
)
from config import MAL_ID_PREFIX
from run import app


@pytest.fixture
def test_app():
    """
    Set up the test class
    """
    app.config["SECRET"] = "Testing Secret"
    app.config["TESTING"] = True
    return app


@pytest_asyncio.fixture
async def client(test_app):
    async with test_app.test_client() as client:
        yield client


# ----- ID Handling -----
def test_handle_mal_id():
    content_id, episode = handle_content_id(f"{MAL_ID_PREFIX}12345")
    assert content_id == "12345"
    assert episode == 1


def test_handle_kitsu_id():
    content_id, episode = handle_content_id("kitsu:1")
    assert content_id == 1
    assert episode == 1


def test_handle_kitsu_id_with_episode():
    content_id, episode = handle_content_id("kitsu:1:2")
    assert content_id == 1
    assert episode == 2


def test_handle_no_mal_id():
    content_id, episode = handle_content_id(f"kitsu:{sys.maxsize}")
    assert content_id is None
    assert episode == -1


def test_handle_invalid_id():
    content_id, episode = handle_content_id("12345")
    assert content_id is None
    assert episode == -1


# ----- Content Sync / Route Tests -----
@pytest.mark.asyncio
@patch("app.routes.mal_client.get_anime_details")
@patch("app.routes.mal_client.update_watched_status")
async def test_addon_content_sync_valid_movie_update(_, mock_get_anime_details, client):
    mock_get_anime_details.return_value = {
        "num_episodes": 1,
        "my_list_status": {"status": "watching", "num_episodes_watched": 0},
    }

    response = await client.get("123/subtitles/anime/kitsu:12345.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.OK.value


@pytest.mark.asyncio
@patch("app.routes.mal_client.get_anime_details")
@patch("app.routes.mal_client.update_watched_status")
@patch("app.routes.content_sync.get_valid_user")
async def test_update_untracked_anime_when_enabled(
    mock_get_user, _, mock_get_anime_details, client
):
    mock_get_user.return_value = {"track_unlisted_anime": True}, None
    mock_get_anime_details.return_value = {
        "num_episodes": 1,
        "my_list_status": None,
    }

    response = await client.get("123/subtitles/anime/kitsu:12345.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.OK.value


@pytest.mark.asyncio
@patch("app.routes.mal_client.get_anime_details")
@patch("app.routes.mal_client.update_watched_status")
@patch("app.routes.content_sync.get_valid_user")
async def test_update_untracked_anime_when_disabled(
    mock_get_user, _, mock_get_anime_details, client
):
    mock_get_user.return_value = {"track_unlisted_anime": False}, None
    mock_get_anime_details.return_value = {
        "num_episodes": 1,
        "my_list_status": None,
    }

    response = await client.get("123/subtitles/anime/kitsu:12345.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.NOT_LIST.value


@pytest.mark.asyncio
@patch("app.routes.mal_client.get_anime_details")
@patch("app.routes.mal_client.update_watched_status")
async def test_addon_content_sync_valid_movie_set_watched(
    _, mock_get_anime_details, client
):
    mock_get_anime_details.return_value = {
        "num_episodes": 1,
        "my_list_status": {"status": "watching", "num_episodes_watched": 1},
    }

    response = await client.get("123/subtitles/anime/kitsu:12345.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.OK.value


@pytest.mark.asyncio
@patch("app.routes.mal_client.get_anime_details")
@patch("app.routes.mal_client.update_watched_status")
async def test_addon_content_sync_valid_movie_no_update(
    _, mock_get_anime_details, client
):
    mock_get_anime_details.return_value = {
        "num_episodes": 1,
        "my_list_status": {"status": "watched", "num_episodes_watched": 1},
    }

    response = await client.get("123/subtitles/anime/kitsu:12345.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.NULL.value


@pytest.mark.asyncio
@patch("app.routes.mal_client.get_anime_details")
@patch("app.routes.mal_client.update_watched_status")
async def test_addon_content_sync_valid_series_update(
    _, mock_get_anime_details, client
):
    mock_get_anime_details.return_value = {
        "num_episodes": 3,
        "my_list_status": {"status": "watching", "num_episodes_watched": 2},
    }

    response = await client.get("123/subtitles/anime/kitsu:12345:3.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.OK.value


@pytest.mark.asyncio
@patch("app.routes.mal_client.get_anime_details")
@patch("app.routes.mal_client.update_watched_status")
async def test_addon_content_sync_valid_series_no_update(
    _, mock_get_anime_details, client
):
    mock_get_anime_details.return_value = {
        "num_episodes": 3,
        "my_list_status": {"status": "watching", "num_episodes_watched": 2},
    }

    response = await client.get("123/subtitles/anime/kitsu:12345:2.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.NULL.value


# ----- Watch Dates -----
def test_start_date_set_on_new_watch():
    my_list_status = {
        "status": "watching",
        "num_episodes_watched": 0,
        "start_date": None,
        "finish_date": None,
    }

    start_date, finish_date = determine_watch_dates(my_list_status, 1, 3)
    assert start_date == datetime.now().strftime("%Y-%m-%d")
    assert finish_date is None


def test_finish_date_set_on_completed():
    my_list_status = {
        "status": "watching",
        "num_episodes_watched": 0,
        "start_date": None,
        "finish_date": None,
    }

    start_date, finish_date = determine_watch_dates(my_list_status, 3, 3)
    assert start_date is None
    assert finish_date == datetime.now().strftime("%Y-%m-%d")


def test_dates_already_set():
    my_list_status = {
        "status": "watching",
        "num_episodes_watched": 0,
        "start_date": "2022-01-01",
        "finish_date": "2022-01-02",
    }

    start_date, finish_date = determine_watch_dates(my_list_status, 1, 3)
    assert start_date == "2022-01-01"
    assert finish_date == "2022-01-02"


# ----- Current Status -----
@pytest.mark.parametrize(
    "current_status,current_ep,watched,total,expected",
    [
        ("plan_to_watch", 0, 0, 3, None),
        ("plan_to_watch", 1, 0, 3, "watching"),
        ("plan_to_watch", 3, 2, 3, "completed"),
        ("on_hold", 1, 0, 3, "watching"),
        ("on_hold", 3, 2, 3, "completed"),
        ("watching", 2, 1, 3, "watching"),
        ("watching", 3, 2, 3, "completed"),
    ],
)
def test_handle_current_status(current_status, current_ep, watched, total, expected):
    assert handle_current_status(current_status, current_ep, watched, total) == expected
