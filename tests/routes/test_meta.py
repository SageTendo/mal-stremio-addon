import pytest

import app.services.anime_mapping as mapping_module


def _stub_kitsu_entry(monkeypatch, *, identifier_type, identifier, mal_id=555, kitsu_id=77):
    entry = mapping_module.MappingEntry(
        identifier_type=identifier_type,
        identifier=identifier,
        kitsu_id=kitsu_id,
        from_season=1,
        from_episode=1,
    )
    monkeypatch.setattr(mapping_module, "_kitsu_forward", {kitsu_id: {identifier_type: entry}})
    reverse = {t: {} for t in mapping_module.PRIORITY}
    reverse[identifier_type][identifier] = [entry]
    monkeypatch.setattr(mapping_module, "_kitsu_reverse", reverse)
    monkeypatch.setattr(mapping_module, "_mal_forward", {})
    monkeypatch.setattr(
        mapping_module, "_mal_reverse", {t: {} for t in mapping_module.PRIORITY}
    )
    monkeypatch.setattr(mapping_module, "_kitsu_to_mal", {kitsu_id: mal_id})
    monkeypatch.setattr(mapping_module, "_mal_to_kitsu", {mal_id: kitsu_id})


@pytest.mark.asyncio
async def test_meta_with_imdb_id_resolves_to_mapped_anime(client, monkeypatch):
    _stub_kitsu_entry(monkeypatch, identifier_type="imdb", identifier="tt7654321")

    response = await client.get("123/meta/anime/tt7654321.json")
    assert response.status_code == 200
    data = await response.json

    assert data["meta"]["id"] == "tt7654321"
    assert len(data["meta"]["videos"]) == 2


@pytest.mark.asyncio
async def test_meta_with_tvdb_id_resolves_to_mapped_anime(client, monkeypatch):
    _stub_kitsu_entry(monkeypatch, identifier_type="tvdb", identifier="99999")

    response = await client.get("123/meta/anime/tvdb:99999.json")
    assert response.status_code == 200
    data = await response.json

    assert data["meta"]["id"] == "tvdb:99999"


@pytest.mark.asyncio
async def test_meta_with_unmapped_imdb_id_returns_empty_meta(client, monkeypatch):
    monkeypatch.setattr(mapping_module, "_kitsu_forward", {})
    monkeypatch.setattr(
        mapping_module, "_kitsu_reverse", {t: {} for t in mapping_module.PRIORITY}
    )
    monkeypatch.setattr(mapping_module, "_mal_forward", {})
    monkeypatch.setattr(
        mapping_module, "_mal_reverse", {t: {} for t in mapping_module.PRIORITY}
    )

    response = await client.get("123/meta/anime/tt0000000.json")
    data = await response.json
    assert data["meta"] == {}


@pytest.mark.asyncio
async def test_meta(client):
    """Test valid meta request."""
    response = await client.get("123/meta/anime/mal:12345.json")
    assert response.status_code == 200
    response_data = await response.json

    assert "meta" in response_data
    assert response_data["meta"]["id"] == "mal:12345"
    assert response_data["meta"]["name"] == "anime title"
    assert response_data["meta"]["type"] == "series"
    assert response_data["meta"]["genres"] == ["Comedy", "Sci-Fi"]
    assert response_data["meta"]["links"] is not None
    assert response_data["meta"]["poster"] == "poster url"
    assert response_data["meta"]["background"] == "cover url"
    assert response_data["meta"]["imdbRating"] == "82.24"
    assert response_data["meta"]["releaseInfo"] == "1998-1999"
    assert response_data["meta"]["description"] == "anime-synopsis"
    assert "videos" in response_data["meta"]
    assert len(response_data["meta"]["videos"]) == 2
