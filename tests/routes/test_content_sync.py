import sys
from datetime import datetime
from tkinter import W
from unittest.mock import MagicMock, patch

from mal import Anime, WatchStatus
import pytest

from app.lib.content_sync import (
    UpdateStatus,
    handle_content_id,
    handle_current_status,
    determine_watch_dates,
)
from config import MAL_ID_PREFIX


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
@patch("app.services.mal_service.MalService.get_anime_details")
@patch("app.services.mal_service.MalService.update_watch_status")
async def test_addon_content_sync_valid_movie_update(
    mock_update_watch_status, mock_anime, client
):
    mock_anime.return_value = Anime(
        {
            "id": "12345",
            "title": {
                "english": "Title",
                "japanese": "Title",
                "synonyms": [],
            },
            "num_episodes": 1,
            "my_list_status": {
                "status": "plan_to_watch",
                "num_episodes_watched": 0,
            },
        }
    )
    mock_update_watch_status.return_value = WatchStatus(
        data={
            "status": "completed",
            "num_episodes_watched": 1,
        },
        anime_id="12345",
    )

    response = await client.get("123/subtitles/anime/kitsu:12345.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.OK.value


@pytest.mark.asyncio
@patch("app.services.mal_service.MalService.get_anime_details")
@patch("app.services.mal_service.MalService.update_watch_status")
@patch("app.routes.content_sync.get_valid_user")
async def test_update_untracked_anime_when_enabled(
    mock_user, mock_update_watch_status, mock_get_anime_details, client
):
    mock_user.return_value = {"track_unlisted_anime": True}, None
    mock_get_anime_details.return_value = Anime(
        {
            "id": "12345",
            "title": {
                "english": "Title",
                "japanese": "Title",
                "synonyms": [],
            },
            "num_episodes": 2,
            "my_list_status": None,
        }
    )
    mock_update_watch_status.return_value = WatchStatus(
        data={
            "status": "watching",
            "num_episodes_watched": 1,
        },
        anime_id="12345",
    )

    response = await client.get("123/subtitles/anime/kitsu:12345.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.OK.value


@pytest.mark.asyncio
@patch("app.services.mal_service.MalService.get_anime_details")
@patch("app.services.mal_service.MalService.update_watch_status")
@patch("app.routes.content_sync.get_valid_user")
async def test_update_untracked_anime_when_disabled(
    mock_get_user, mock_update_watch_status, mock_get_anime_details, client
):
    mock_get_user.return_value = {"track_unlisted_anime": False}, None
    mock_get_anime_details.return_value = Anime(
        {
            "id": "12345",
            "title": {
                "english": "Title",
                "japanese": "Title",
                "synonyms": [],
            },
            "num_episodes": 2,
            "my_list_status": None,
        }
    )
    mock_update_watch_status.return_value = WatchStatus(
        data={
            "status": "watching",
            "num_episodes_watched": 1,
        },
        anime_id="12345",
    )

    response = await client.get("123/subtitles/anime/kitsu:12345.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.NOT_LIST.value


@pytest.mark.asyncio
@patch("app.services.mal_service.MalService.get_anime_details")
@patch("app.services.mal_service.MalService.update_watch_status")
async def test_addon_content_sync_valid_movie_set_watched(
    mock_update_watch_status, mock_get_anime_details, client
):
    mock_get_anime_details.return_value = Anime(
        {
            "id": "12345",
            "title": {
                "english": "Title",
                "japanese": "Title",
                "synonyms": [],
            },
            "num_episodes": 1,
            "my_list_status": {"status": "watching", "num_episodes_watched": 1},
        }
    )
    mock_update_watch_status.return_value = WatchStatus(
        data={
            "status": "completed",
            "num_episodes_watched": 1,
        },
        anime_id="12345",
    )

    response = await client.get("123/subtitles/anime/kitsu:12345.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.OK.value


@pytest.mark.asyncio
@patch("app.services.mal_service.MalService.get_anime_details")
@patch("app.services.mal_service.MalService.update_watch_status")
async def test_addon_content_sync_valid_movie_no_update(
    mock_update_watch_status, mock_get_anime_details, client
):
    mock_get_anime_details.return_value = Anime(
        {
            "id": "12345",
            "title": {
                "english": "Title",
                "japanese": "Title",
                "synonyms": [],
            },
            "num_episodes": 1,
            "my_list_status": {"status": "completed", "num_episodes_watched": 1},
        }
    )
    mock_update_watch_status.return_value = WatchStatus(
        data={
            "status": "completed",
            "num_episodes_watched": 1,
        },
        anime_id="12345",
    )

    response = await client.get("123/subtitles/anime/kitsu:12345.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.NULL.value


@pytest.mark.asyncio
@patch("app.services.mal_service.MalService.get_anime_details")
@patch("app.services.mal_service.MalService.update_watch_status")
async def test_addon_content_sync_valid_series_update(
    mock_update_watch_status, mock_get_anime_details, client
):
    mock_get_anime_details.return_value = Anime(
        {
            "id": "12345",
            "title": {
                "english": "Title",
                "japanese": "Title",
                "synonyms": [],
            },
            "num_episodes": 3,
            "my_list_status": {"status": "watching", "num_episodes_watched": 1},
        }
    )
    mock_update_watch_status.return_value = WatchStatus(
        data={
            "status": "watching",
            "num_episodes_watched": 2,
        },
        anime_id="12345",
    )

    response = await client.get("123/subtitles/anime/kitsu:12345:3.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.OK.value


@pytest.mark.asyncio
@patch("app.services.mal_service.MalService.get_anime_details")
@patch("app.services.mal_service.MalService.update_watch_status")
async def test_addon_content_sync_valid_series_no_update(
    mock_update_watch_status, mock_get_anime_details, client
):
    mock_get_anime_details.return_value = Anime(
        {
            "id": "12345",
            "title": {
                "english": "Title",
                "japanese": "Title",
                "synonyms": [],
            },
            "num_episodes": 3,
            "my_list_status": {"status": "watching", "num_episodes_watched": 2},
        }
    )
    mock_update_watch_status.return_value = WatchStatus(
        data={
            "status": "watching",
            "num_episodes_watched": 2,
        },
        anime_id="12345",
    )

    response = await client.get("123/subtitles/anime/kitsu:12345:2.json")
    assert response.status_code == 200

    data = await response.json
    assert "message" in data
    assert data["subtitles"][0]["lang"] == UpdateStatus.NULL.value


# ----- Watch Dates -----
def test_start_date_set_on_new_watch():
    anime = Anime(
        {
            "id": "12345",
            "title": {
                "english": "Title",
                "japanese": "Title",
                "synonyms": [],
            },
            "num_episodes": 3,
            "my_list_status": {
                "status": "watching",
                "num_episodes_watched": 0,
                "start_date": None,
                "finish_date": None,
            },
        }
    )
    assert anime.my_list_status is not None
    assert anime.num_episodes is not None

    start_date, finish_date = determine_watch_dates(
        anime.my_list_status,
        current_episode=1,
        total_episodes=anime.num_episodes,
    )
    assert start_date == datetime.now().strftime("%Y-%m-%d")
    assert not finish_date


def test_finish_date_set_on_completed():
    anime = Anime(
        {
            "id": "12345",
            "title": {
                "english": "Title",
                "japanese": "Title",
                "synonyms": [],
            },
            "num_episodes": 3,
            "my_list_status": {"status": "watching", "num_episodes_watched": 3},
        }
    )
    assert anime.my_list_status is not None

    start_date, finish_date = determine_watch_dates(
        anime.my_list_status,
        current_episode=3,
        total_episodes=3,
    )
    assert not start_date
    assert finish_date == datetime.now().strftime("%Y-%m-%d")


def test_dates_already_set():
    my_list_status = WatchStatus(
        data={
            "status": "watching",
            "num_episodes_watched": 0,
            "start_date": "2022-01-01",
            "finish_date": "2022-01-02",
        },
        anime_id="12345",
    )

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
