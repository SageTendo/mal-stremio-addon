from unittest.mock import patch

import pytest
import pytest_asyncio

from app.routes.manifest import MANIFEST
from run import app


@pytest.mark.asyncio
async def test_manifest(client):
    response = await client.get("/123/manifest.json")
    assert response.status_code == 200

    manifest = await response.json
    assert manifest["id"] is not None
    assert manifest["name"] is not None
    assert manifest["version"] is not None
    assert manifest["logo"] is not None
    assert manifest["description"] is not None
    assert manifest["types"] is not None
    assert manifest["catalogs"] is not None
    assert manifest["behaviorHints"] is not None
    assert manifest["resources"] is not None
    assert manifest["idPrefixes"] is not None

    for catalog in manifest["catalogs"]:
        assert catalog["type"] == "anime"
        assert catalog["id"] in [
            "search_list",
            "plan_to_watch",
            "watching",
            "completed",
            "on_hold",
            "dropped",
            "seasonal",
        ]
        assert catalog["name"] in [
            "MAL",
            "MAL: Plan To Watch",
            "MAL: Watching",
            "MAL: Completed",
            "MAL: On Hold",
            "MAL: Dropped",
            "MAL: Seasonal",
        ]

        for extra in catalog["extra"]:
            assert extra["name"] in ["skip", "genre", "search", "season"]

            if extra.get("isRequired") is not None:
                if extra["name"] == "genre":
                    assert extra["isRequired"] is False
                elif extra["name"] == "search":
                    assert extra["isRequired"] is True

            if extra.get("options") is not None:
                assert extra["options"] is not None


@pytest.mark.asyncio
async def test_unconfigured_manifest(client):
    response = await client.get("/manifest.json")
    assert response.status_code == 200

    manifest = await response.json
    assert manifest["behaviorHints"]["configurable"] is True
    assert manifest["behaviorHints"]["configurationRequired"] is True


@pytest.mark.asyncio
async def test_configured_manifest(client):
    response = await client.get("/123/manifest.json")
    assert response.status_code == 200
    assert await response.json is not None


@pytest.mark.asyncio
@patch("app.routes.manifest.get_user")
async def test_catalog_filtering(mock_user, client):
    mock_user.return_value = {"catalogs": ["watching"]}
    async with client.session_transaction() as sess:
        sess["user"] = {"uid": "123", "refresh_token": "test_refresh_token"}

    response = await client.get("/123/manifest.json")
    assert response.status_code == 200

    data = await response.json
    assert len(data["catalogs"]) == 2


@pytest.mark.asyncio
@patch("app.routes.manifest.get_user")
async def test_catalog_filtering_no_user_catalogs(mock_user, client):
    mock_user.return_value = {"catalogs": None}
    async with client.session_transaction() as sess:
        sess["user"] = {"uid": "123", "refresh_token": "test_refresh_token"}

    response = await client.get("/123/manifest.json")
    assert response.status_code == 200
    data = await response.json
    assert len(data["catalogs"]) == len(MANIFEST["catalogs"])


@pytest.mark.asyncio
@patch("app.routes.manifest.get_user")
async def test_catalog_filtering_no_catalogs(mock_user, client):
    mock_user.return_value = {"catalogs": []}
    async with client.session_transaction() as sess:
        sess["user"] = {"uid": "123", "refresh_token": "test_refresh_token"}

    response = await client.get("/123/manifest.json")
    assert response.status_code == 200

    data = await response.json
    assert len(data["catalogs"]) == 1


@pytest.mark.asyncio
@patch("app.routes.manifest.get_user")
async def test_catalog_filtering_invalid_catalog(mock_user, client):
    mock_user.return_value = {"catalogs": ["invalid catalog"]}
    async with client.session_transaction() as sess:
        sess["user"] = {"uid": "123", "refresh_token": "test_refresh_token"}

    response = await client.get("/123/manifest.json")
    assert response.status_code == 200

    data = await response.json
    assert len(data["catalogs"]) == 1
