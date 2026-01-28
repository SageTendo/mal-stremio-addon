from re import M
from unittest.mock import AsyncMock, MagicMock, patch

from mal import Anime, Client
import pytest
import pytest_asyncio

from app.factory import create_app
from app.services.mal_service import MalService
from config import MAL_ID_PREFIX
from run import app


class MockMalService(MalService):
    DUMMY_MAL_RESPONSE = {
        "data": [
            {
                "id": 1,
                "node": {
                    "title": "Naruto",
                    "alternative_titles": {
                        "en": "Naruto",
                        "ja": "なると",
                        "synonyms": ["Naruto"],
                    },
                    "mean": 8.5,
                    "synopsis": "Naruto anime",
                    "main_picture": {"large": "http://example.com/poster.jpg"},
                    "pictures": [
                        {"large": "http://example.com/poster1.jpg"},
                        {"large": "http://example.com/poster2.jpg"},
                        {"large": "http://example.com/poster3.jpg"},
                    ],
                    "genres": [{"name": "Action"}],
                    "start_date": "2002-02-15",
                    "end_date": "2002-02-15",
                    "media_type": "tv",
                },
            },
            {
                "id": 2,
                "node": {
                    "title": "Naruto Shippuden",
                    "alternative_titles": {
                        "en": "Naruto Shippuden",
                        "ja": "なるとしょうがうなるとしょうがう",
                        "synonyms": ["Shippuden"],
                    },
                    "mean": 8.5,
                    "synopsis": "Naruto Shippuden anime",
                    "main_picture": {"large": "http://example.com/poster.jpg"},
                    "pictures": [
                        {"large": "http://example.com/poster1.jpg"},
                        {"medium": "http://example.com/poster2.jpg"},
                        {"large": "http://example.com/poster3.jpg"},
                    ],
                    "genres": [{"name": "Action"}],
                    "start_date": "2002-02-15",
                    "end_date": "2002-02-15",
                    "media_type": "ova",
                },
            },
            {
                "id": 3,
                "node": {
                    "title": "Naruto Shippuden",
                    "alternative_titles": {
                        "en": "Naruto Shippuden",
                        "ja": "なるとしょうがうなるとしょうがう",
                        "synonyms": ["Shippuden"],
                    },
                    "mean": 8.5,
                    "synopsis": "Naruto Shippuden anime",
                    "main_picture": {"large": "http://example.com/poster.jpg"},
                    "pictures": [{"large": "http://example.com/poster1.jpg"}],
                    "genres": [{"name": "Action"}],
                    "start_date": None,
                    "end_date": None,
                    "media_type": "movie",
                },
            },
            {
                "id": 4,
                "node": {
                    "title": "Naruto Shippuden",
                    "alternative_titles": {
                        "en": "Naruto Shippuden",
                        "ja": "なるとしょうがうなるとしょうがう",
                        "synonyms": ["Shippuden"],
                    },
                    "mean": 8.5,
                    "synopsis": "Naruto Shippuden anime",
                    "main_picture": {"large": "http://example.com/poster.jpg"},
                    "pictures": [{"medium": "http://example.com/poster2.jpg"}],
                    "genres": [{"name": "Action"}],
                    "start_date": "2002-02-15",
                    "end_date": "2002-02-15",
                    "media_type": "special",
                },
            },
            {
                "id": 5,
                "node": {
                    "title": "Naruto Shippuden",
                    "alternative_titles": {
                        "en": "Naruto Shippuden",
                        "ja": "なるとしょうがうなるとしょうがう",
                        "synonyms": ["Shippuden"],
                    },
                    "mean": None,
                    "synopsis": "Naruto Shippuden anime",
                    "main_picture": {"medium": "http://example.com/poster.jpg"},
                    "pictures": [{"large": "http://example.com/poster3.jpg"}],
                    "genres": [{"name": "Action"}],
                    "start_date": "2002-02-15",
                    "end_date": None,
                    "media_type": "unknown",
                },
            },
            {
                "id": 6,
                "node": {
                    "title": "Naruto Shippuden",
                    "alternative_titles": {
                        "en": "Naruto Shippuden",
                        "ja": "なるとしょうがうなるとしょうがう",
                        "synonyms": ["Shippuden"],
                    },
                    "mean": 8.5,
                    "synopsis": "Naruto Shippuden anime",
                    "main_picture": {"large": "http://example.com/poster.jpg"},
                    "pictures": [{"large": "http://example.com/poster1.jpg"}],
                    "genres": [{"name": "Action"}],
                    "start_date": "2002-02-15",
                    "end_date": "2002-02-15",
                    "media_type": "movie",
                },
            },
        ]
    }

    def __init__(self):
        super().__init__()
        self.client = MagicMock()

    async def start(self):
        pass

    async def stop(self):
        pass

    async def search_anime(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        nsfw: bool = False,
        genre: str = "",
    ):
        return list(map(lambda x: Anime(x["node"]), self.DUMMY_MAL_RESPONSE["data"]))

    async def get_user_anime_list(self, **kwargs):
        return list(map(lambda x: Anime(x["node"]), self.DUMMY_MAL_RESPONSE["data"]))


@pytest.fixture
def test_app():
    """
    Set up the test class
    """
    app = create_app()
    app.config["SECRET"] = "Testing Secret"
    app.config["TESTING"] = True
    app.mal = MockMalService()
    app.mal.client = AsyncMock()
    return app


@pytest_asyncio.fixture
async def client(test_app):
    async with test_app.test_client() as client:
        yield client


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
