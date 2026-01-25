from unittest.mock import patch

import pytest
import pytest_asyncio

from config import MAL_ID_PREFIX
from run import app

DUMMY_MAL_RESPONSE = {
    "data": [
        {
            "node": {
                "id": 1,
                "title": "Naruto",
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
            }
        },
        {
            "node": {
                "id": 2,
                "title": "Naruto Shippuden",
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
            }
        },
        {
            "node": {
                "id": 3,
                "title": "Naruto Shippuden",
                "mean": 8.5,
                "synopsis": "Naruto Shippuden anime",
                "main_picture": {"large": "http://example.com/poster.jpg"},
                "pictures": [{"large": "http://example.com/poster1.jpg"}],
                "genres": [{"name": "Action"}],
                "start_date": None,
                "end_date": None,
                "media_type": "movie",
            }
        },
        {
            "node": {
                "id": 4,
                "title": "Naruto Shippuden",
                "mean": 8.5,
                "synopsis": "Naruto Shippuden anime",
                "main_picture": {"large": "http://example.com/poster.jpg"},
                "pictures": [{"medium": "http://example.com/poster2.jpg"}],
                "genres": [{"name": "Action"}],
                "start_date": "2002-02-15",
                "end_date": "2002-02-15",
                "media_type": "special",
            }
        },
        {
            "node": {
                "id": 5,
                "title": "Naruto Shippuden",
                "mean": None,
                "synopsis": "Naruto Shippuden anime",
                "main_picture": {"medium": "http://example.com/poster.jpg"},
                "pictures": [{"large": "http://example.com/poster3.jpg"}],
                "genres": [{"name": "Action"}],
                "start_date": "2002-02-15",
                "end_date": None,
                "media_type": "unknown",
            }
        },
        {
            "node": {
                "id": 6,
                "title": "Naruto Shippuden",
                "mean": 8.5,
                "synopsis": "Naruto Shippuden anime",
                "main_picture": {"large": "http://example.com/poster.jpg"},
                "pictures": [{"large": "http://example.com/poster1.jpg"}],
                "genres": [{"name": "Action"}],
                "start_date": "2002-02-15",
                "end_date": "2002-02-15",
                "media_type": "movie",
            }
        },
    ]
}


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
@patch("app.routes.mal_client.get_user_anime_list")
@patch("app.routes.mal_client.get_anime_list")
async def test_catalog(mock_get_user_anime_list, mock_get_anime_list, client):
    """Test valid catalog request."""
    mock_get_user_anime_list.return_value = DUMMY_MAL_RESPONSE
    mock_get_anime_list.return_value = DUMMY_MAL_RESPONSE

    response = await client.get("123/catalog/anime/watching.json")
    assert response.status_code == 200
    response_data = await response.json
    _meta_asserts(response_data)


@pytest.mark.asyncio
@patch("app.routes.mal_client.get_anime_list")
async def test_search(mock_get_anime_list, client):
    """Test catalog request with a search query."""
    mock_get_anime_list.return_value = DUMMY_MAL_RESPONSE

    response = await client.get("123/catalog/anime/search_list/search=Naruto.json")
    assert response.status_code == 200

    response_data = await response.json
    assert len(response_data["metas"]) > 0
    _meta_asserts(response_data)

    # Test bad request
    response = await client.get("123/catalog/anime/search_list/search=N.json")
    assert response.status_code == 400


@pytest.mark.asyncio
@patch("app.routes.mal_client.get_user_anime_list")
async def test_genre_filtering_no_results(mock_get_user_anime_list, client):
    """Test catalog request with a search query."""
    mock_get_user_anime_list.return_value = DUMMY_MAL_RESPONSE

    response = await client.get("123/catalog/anime/watching/genre=Adventure.json")
    assert response.status_code == 200
    response_data = await response.json
    assert len(response_data["metas"]) == 0


@pytest.mark.asyncio
@patch("app.routes.mal_client.get_user_anime_list")
async def test_genre_filtering(mock_get_user_anime_list, client):
    """Test catalog request with a search query."""
    mock_get_user_anime_list.return_value = DUMMY_MAL_RESPONSE

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
