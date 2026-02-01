from unittest.mock import AsyncMock, MagicMock

from mal import Anime, WatchStatus
import pytest
import pytest_asyncio
from app.factory import create_app
from app.services.mal_service import MalService


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
