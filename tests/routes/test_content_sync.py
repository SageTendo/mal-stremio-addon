import sys
from datetime import datetime
from unittest.mock import AsyncMock, patch

from mal import Anime, WatchStatus
import pytest

import app.services.anime_mapping as mapping_module
from app.lib.content_sync import (
    UpdateStatus,
    handle_content_id,
    handle_current_status,
    determine_watch_dates,
)
from config import MAL_ID_PREFIX


# ----- ID Handling -----
@pytest.mark.asyncio
async def test_handle_mal_id():
    content_id, episode = await handle_content_id(f"{MAL_ID_PREFIX}12345")
    assert content_id == "12345"
    assert episode == 1


@pytest.mark.asyncio
async def test_handle_kitsu_id():
    content_id, episode = await handle_content_id("kitsu:1")
    assert content_id == "1"
    assert episode == 1


@pytest.mark.asyncio
async def test_handle_kitsu_id_with_episode():
    content_id, episode = await handle_content_id("kitsu:1:2")
    assert content_id == "1"
    assert episode == 2


@pytest.mark.asyncio
async def test_handle_no_mal_id():
    content_id, episode = await handle_content_id(f"kitsu:{sys.maxsize}")
    assert content_id is None
    assert episode == -1


@pytest.mark.asyncio
async def test_handle_invalid_id():
    content_id, episode = await handle_content_id("12345")
    assert content_id is None
    assert episode == -1


@pytest.mark.asyncio
async def test_handle_imdb_id_without_season_episode_is_invalid():
    content_id, episode = await handle_content_id("tt0123456")
    assert content_id is None
    assert episode == -1


def _stub_single_kitsu_entry(monkeypatch, *, identifier_type, identifier):
    """Isolate a single fake kitsu-keyed mapping entry for the duration of a
    test, without disturbing the real mapping data other tests in this file
    rely on (loaded as a side effect of `test_auth`/`test_catalog` importing
    `run`)."""
    entry = mapping_module.MappingEntry(
        identifier_type=identifier_type,
        identifier=identifier,
        kitsu_id=42,
        from_season=1,
        from_episode=1,
    )
    monkeypatch.setattr(mapping_module, "_kitsu_forward", {42: {identifier_type: entry}})
    reverse = {t: {} for t in mapping_module.PRIORITY}
    reverse[identifier_type][identifier] = [entry]
    monkeypatch.setattr(mapping_module, "_kitsu_reverse", reverse)
    monkeypatch.setattr(mapping_module, "_mal_forward", {})
    monkeypatch.setattr(
        mapping_module, "_mal_reverse", {t: {} for t in mapping_module.PRIORITY}
    )
    monkeypatch.setattr(mapping_module, "_kitsu_to_mal", {42: 99})


@pytest.mark.asyncio
async def test_handle_imdb_id_resolves_via_flat_offset(monkeypatch):
    _stub_single_kitsu_entry(monkeypatch, identifier_type="imdb", identifier="tt0123456")

    content_id, episode = await handle_content_id("tt0123456:1:5")
    assert content_id == "99"
    assert episode == 5


@pytest.mark.asyncio
async def test_handle_imdb_id_refines_via_cinemeta_full_fidelity(monkeypatch):
    _stub_single_kitsu_entry(monkeypatch, identifier_type="imdb", identifier="tt0123456")

    cinemeta_service = AsyncMock()
    cinemeta_service.get_season_episode_videos.return_value = [
        {"season": 1, "episode": e} for e in range(1, 13)
    ] + [{"season": 2, "episode": e} for e in range(1, 14)]

    content_id, episode = await handle_content_id("tt0123456:2:1", cinemeta_service)
    assert content_id == "99"
    assert episode == 13


@pytest.mark.asyncio
async def test_handle_tvdb_id_resolves_via_flat_offset(monkeypatch):
    _stub_single_kitsu_entry(monkeypatch, identifier_type="tvdb", identifier="12345")

    content_id, episode = await handle_content_id("tvdb:12345:1:3")
    assert content_id == "99"
    assert episode == 3


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
        ("plan_to_watch", 0, 0, 0, None),
        ("watching", 0, 0, 0, None),
        ("on_hold", 0, 0, 0, None),
        ("completed", 0, 0, 0, None),
        ("completed", 1, 1, 0, None),
        ("on_hold", 1, 1, 0, None),
        ("watching", 1, 1, 0, None),
        ("plan_to_watch", 1, 1, 0, None),
        ("completed", 1, 0, 0, None),
        ("plan_to_watch", 1, 0, 0, "watching"),
        ("watching", 1, 0, 0, "watching"),
        ("on_hold", 1, 0, 0, "watching"),
    ],
)
def test_handle_current_status(current_status, current_ep, watched, total, expected):
    assert handle_current_status(current_status, current_ep, watched, total) == expected
