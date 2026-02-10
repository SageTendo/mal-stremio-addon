import pytest


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
