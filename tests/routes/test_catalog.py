from re import M
from unittest.mock import AsyncMock, MagicMock, patch

from mal import Anime, Client
import pytest
import pytest_asyncio

from app.factory import create_app
from app.services.mal_service import MalService
from config import MAL_ID_PREFIX
from run import app


def _meta_asserts(response_data):
    assert "metas" in response_data

    for anime in response_data["metas"]:
        assert "id" in anime
        assert MAL_ID_PREFIX in anime["id"]
        assert "name" in anime
        assert anime["name"] is not None

        assert "type" in anime
        assert anime["type"] in ["series", "movie"]

        assert "genres" in anime
        assert anime["genres"] is not None

        assert "links" in anime
        assert anime["links"][0]["name"] == "Action"
        assert anime["links"][0]["url"] is not None

        assert "poster" in anime
        assert anime["poster"] == "http://example.com/poster.jpg"

        assert "imdbRating" in anime
        assert anime["imdbRating"] in ["8.5", None]

        assert "background" in anime
        assert anime["background"] in [
            "http://example.com/poster1.jpg",
            "http://example.com/poster2.jpg",
            "http://example.com/poster3.jpg",
        ]

        assert "releaseInfo" in anime
        assert anime["releaseInfo"] in ["2002-", "2002-2002", None]

        assert "description" in anime
        assert anime["description"] in [
            "Naruto anime",
            "Naruto Shippuden anime",
            None,
        ]


@pytest.mark.asyncio
async def test_catalog(client):
    """Test valid catalog request."""
    response = await client.get("123/catalog/anime/watching.json")
    assert response.status_code == 200
    response_data = await response.json
    _meta_asserts(response_data)


@pytest.mark.asyncio
async def test_search(client):
    """Test catalog request with a search query."""
    response = await client.get("123/catalog/anime/search_list/search=Naruto.json")
    assert response.status_code == 200

    response_data = await response.json
    assert len(response_data["metas"]) > 0
    _meta_asserts(response_data)


@pytest.mark.asyncio
async def test_genre_filtering_no_results(client):
    """Test catalog request with a search query."""
    response = await client.get("123/catalog/anime/watching/genre=Adventure.json")
    assert response.status_code == 200
    response_data = await response.json
    assert len(response_data["metas"]) == 0


@pytest.mark.asyncio
async def test_genre_filtering(client):
    """Test catalog request with a search query."""
    response = await client.get("123/catalog/anime/watching/genre=Action.json")
    assert response.status_code == 200
    response_data = await response.json
    assert len(response_data["metas"]) > 0
    _meta_asserts(response_data)

    response = await client.get("123/catalog/anime/watching/genre=Boys Love.json")
    assert response.status_code == 200
    response_data = await response.json
    assert len(response_data["metas"]) == 0
    _meta_asserts(response_data)

    response = await client.get(
        "123/catalog/anime/watching/genre={'id':%201,%20'name':%20'Action'}.json"
    )
    assert response.status_code == 200
    response_data = await response.json
    assert len(response_data["metas"]) > 0
    _meta_asserts(response_data)
