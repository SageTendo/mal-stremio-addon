import pytest
from kitsu import Anime as KitsuAnime

import app.services.anime_mapping as mapping_module
from app.lib.content_sync import handle_content_id
from app.services.kitsu_service import KitsuService
from tests.conftest import MockKitsuService


@pytest.mark.asyncio
async def test_kitsu_fallback_video_id_round_trips_through_content_sync(monkeypatch):
    """
    When a title has no Cinemeta mapping, video ids must stay in the flat
    `kitsu:{id}:{episode}` shape content_sync.py's absolute-numbering parser
    expects — not the season-aware `kitsu:{id}:{season}:{episode}` shape used
    for Cinemeta-resolved ids, which would get truncated by
    `_parse_id_and_episode` (parts[:2]) and silently mis-sync watch status.
    """
    monkeypatch.setattr(mapping_module, "_kitsu_forward", {})
    monkeypatch.setattr(mapping_module, "_mal_forward", {})
    monkeypatch.setattr(mapping_module, "_kitsu_to_mal", {1: 42})

    anime = KitsuAnime(MockKitsuService.DUMMY_KITSU_RESPONSE)
    service = KitsuService()
    videos = await service._get_video_metadata(anime)

    assert videos is not None
    video_id = videos[1]["id"]
    assert video_id == "kitsu:1:2"

    content_id, episode = await handle_content_id(video_id)
    assert content_id == "42"
    assert episode == 2
