from unittest.mock import AsyncMock, MagicMock

from mal import Anime as MalAnime, WatchStatus
from kitsu import Anime as KitsuAnime
import pytest
import pytest_asyncio
from app.factory import create_app
from app.services.cinemeta_service import CinemetaService
from app.services.kitsu_service import KitsuService
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
        self._client = MagicMock()

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
        return list(map(lambda x: MalAnime(x["node"]), self.DUMMY_MAL_RESPONSE["data"]))

    async def get_user_anime_list(self, **kwargs):
        return list(map(lambda x: MalAnime(x["node"]), self.DUMMY_MAL_RESPONSE["data"]))


class MockKitsuService(KitsuService):
    DUMMY_KITSU_RESPONSE = data = {
        "data": {
            "id": "1",
            "type": "series",
            "attributes": {
                "createdAt": "2013-02-20T16:00:13.609Z",
                "updatedAt": "2026-02-10T06:00:06.965Z",
                "slug": "anime-slug",
                "synopsis": "anime-synopsis",
                "titles": {
                    "en": "anime title",
                    "en_jp": "anime title jp",
                    "ja_jp": "anime title romaji",
                },
                "canonicalTitle": "Title",
                "abbreviatedTitles": [],
                "averageRating": "82.24",
                "ratingFrequencies": {
                    "2": "4364",
                    "3": "61",
                    "4": "423",
                    "5": "39",
                    "6": "212",
                    "7": "40",
                    "8": "4157",
                    "9": "59",
                    "10": "891",
                    "11": "87",
                    "12": "2596",
                    "13": "175",
                    "14": "9067",
                    "15": "472",
                    "16": "9380",
                    "17": "963",
                    "18": "11436",
                    "19": "882",
                    "20": "37937",
                },
                "userCount": 161153,
                "favoritesCount": 5160,
                "startDate": "1998-04-03",
                "endDate": "1999-04-24",
                "popularityRank": 44,
                "ratingRank": 185,
                "ageRating": "R",
                "ageRatingGuide": "17+ (violence & profanity)",
                "subtype": "TV",
                "status": "finished",
                "episodeCount": 26,
                "episodeLength": 25,
                "totalLength": 626,
                "youtubeVideoId": "yt video id",
                "showType": "TV",
                "nsfw": False,
                "posterImage": {
                    "original": "poster url",
                },
                "coverImage": {
                    "original": "cover url",
                },
            },
        },
        "included": [
            {
                "id": "3",
                "type": "genres",
                "attributes": {
                    "createdAt": "2013-02-20T16:00:15.671Z",
                    "updatedAt": "2013-02-20T16:00:15.671Z",
                    "name": "Comedy",
                    "slug": "comedy",
                },
            },
            {
                "id": "5",
                "type": "genres",
                "attributes": {
                    "createdAt": "2013-02-20T16:00:15.701Z",
                    "updatedAt": "2013-02-20T16:00:15.701Z",
                    "name": "Sci-Fi",
                    "slug": "sci-fi",
                },
            },
            {
                "id": "6",
                "type": "genres",
                "attributes": {
                    "createdAt": "2013-02-20T16:00:15.716Z",
                    "updatedAt": "2013-02-20T16:00:15.716Z",
                    "name": "Space",
                    "slug": "space",
                },
            },
            {
                "id": "229115",
                "type": "episodes",
                "attributes": {
                    "createdAt": "2017-11-23T09:52:14.730Z",
                    "updatedAt": "2021-09-17T05:03:10.398Z",
                    "synopsis": "epsisode synopsis",
                    "description": "episode description",
                    "titles": {
                        "en_jp": "episode title jp",
                        "en_us": "episode title us",
                        "ja_jp": "episode title romaji",
                    },
                    "canonicalTitle": "episode title",
                    "seasonNumber": 1,
                    "number": 1,
                    "relativeNumber": {},
                    "airdate": "1998-10-23",
                    "length": 25,
                    "thumbnail": {
                        "original": "thumbnail url",
                    },
                },
            },
            {
                "id": "229114",
                "type": "episodes",
                "attributes": {
                    "createdAt": "2017-11-23T09:52:14.259Z",
                    "updatedAt": "2021-09-17T05:03:10.217Z",
                    "synopsis": "epsisode synopsis",
                    "description": "episode description",
                    "titles": {
                        "en_jp": "episode title jp",
                        "en_us": "episode title us",
                        "ja_jp": "episode title romaji",
                    },
                    "canonicalTitle": "Stray Dog Strut",
                    "seasonNumber": 1,
                    "number": 2,
                    "relativeNumber": {},
                    "airdate": "1998-10-30",
                    "length": 22,
                    "thumbnail": {
                        "original": "thumbnail url",
                    },
                },
            },
        ],
    }

    def __init__(self):
        super().__init__()
        self._client = MagicMock()

    async def start(self):
        pass

    async def stop(self):
        pass

    async def get_anime_by_id(self, kitsu_id: str, *, include_nsfw: bool = False):
        return KitsuAnime(self.DUMMY_KITSU_RESPONSE)

    async def get_anime_by_title(self, query: str, *, include_nsfw: bool = False):
        return KitsuAnime(self.DUMMY_KITSU_RESPONSE)


class MockCinemetaService(CinemetaService):
    def __init__(self):
        super().__init__()
        self._client = MagicMock()

    async def start(self):
        pass

    async def stop(self):
        pass

    async def get_season_episode_videos(self, imdb_id: str):
        return None


@pytest.fixture
def test_app():
    """
    Set up the test class
    """
    app = create_app()
    app.config["SECRET"] = "Testing Secret"
    app.config["TESTING"] = True
    app.mal = MockMalService()
    app.mal._client = AsyncMock()
    app.kitsu = MockKitsuService()
    app.kitsu._client = AsyncMock()
    app.cinemeta = MockCinemetaService()
    return app


@pytest_asyncio.fixture
async def client(test_app):
    async with test_app.test_client() as client:
        yield client
