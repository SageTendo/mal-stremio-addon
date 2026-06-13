from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio

from app.services.db import get_valid_user
from run import app


@pytest.mark.asyncio
@patch("app.services.db.get_user")
async def test_get_token(mock_get_user, client):
    mock_get_user.return_value = {
        "uid": "123",
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 9999999999,
        "last_updated": datetime.utcnow(),
    }

    user, error = get_valid_user("123")
    assert error is None
    assert user["access_token"] == "test_access_token"


@pytest.mark.asyncio
async def test_user_logged_in(client):
    """
    Test that the user is redirected to the configuration page if they are already logged in
    """
    # Simulate user already logged in
    async with client.session_transaction() as sess:
        sess["user"] = {"uid": "123", "refresh_token": "test_refresh_token"}

    # Call the authorization route
    await client.get("/authorization")

    # Assert that the user is redirected to the home page with a warning flash
    configure_response = await client.get("/configure")
    assert 200 == configure_response.status_code

    data = await configure_response.data
    assert "You are already logged in." in data.decode()


@pytest.mark.asyncio
async def test_user_not_logged_in(client):
    response = await client.get("/authorization")
    assert "/callback" in response.location


@pytest.mark.asyncio
@patch("app.routes.mal_client.get_access_token")
@patch("app.routes.mal_client.get_user_details")
@patch("app.services.db.store_user")
async def test_callback(
    mock_store_user, mock_get_user_details, mock_get_access_token, client
):
    """
    Test that the user is logged in and redirected to configuration page with a success message
    """
    # Mock the access token and user details
    mock_get_access_token.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
        "last_updated": datetime.utcnow(),
    }
    mock_get_user_details.return_value = {"id": "123", "name": "Test User"}
    mock_store_user.return_value = None

    # Simulate the callback with a successful authorization code
    async with client.session_transaction() as sess:
        sess["code_verifier"] = "mocked_verifier"
    response = await client.get(
        "/callback?code=mocked_auth_code", follow_redirects=True
    )
    data = await response.data
    assert "You are now logged in." in data.decode()

    # Check that the user was stored in the session
    async with client.session_transaction() as sess:
        assert "123" == sess["user"]["uid"]
        assert "test_refresh_token" == sess["user"]["refresh_token"]


@pytest.mark.asyncio
@patch("app.routes.mal_client.refresh_token")
@patch("app.services.db.store_user")
async def test_refresh_token(mock_store_user, mock_refresh_token, client):
    """
    Test that the user's session is refreshed and the user is redirected to the configuration page
    """
    # Mock the refresh token response
    mock_refresh_token.return_value = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600,
    }
    mock_store_user.return_value = None

    # Simulate a logged-in user session
    async with client.session_transaction() as sess:
        sess["user"] = {"uid": "123", "refresh_token": "old_refresh_token"}

    # Simulate the refresh endpoint
    response = await client.get("/refresh", follow_redirects=True)
    data = await response.data

    # Manually manage the session after redirect
    async with client.session_transaction() as sess:
        assert "user" in sess
        assert "MyAnimeList session refreshed." in data.decode()
        assert "new_refresh_token" in sess["user"]["refresh_token"]


@pytest.mark.asyncio
async def test_session_expired(client):
    """
    Test that the user is logged out and redirected to the index page with a warning message
    """
    async with client.session_transaction() as sess:
        response = await client.get("/refresh")
        response = await client.get(response.location)
        data = await response.data

        assert "Session expired! Please log in to MyAnimeList again." in data.decode()
        assert sess.get("user") is None


@pytest.mark.asyncio
async def test_logout_not_logged_in(client):
    """
    Test that the user is redirected to the index page with a warning message
    """
    response = await client.get("/logout", follow_redirects=True)
    data = await response.data
    assert "You are not logged in." in data.decode()


@pytest.mark.asyncio
@pytest.mark.order("last")
async def test_logout(client):
    """
    Test that the user is logged out and redirected to the index page
    """
    async with client.session_transaction() as sess:
        sess["user"] = {"uid": "123", "refresh_token": "test_refresh_token"}
        assert "123" == sess["user"]["uid"]
        assert "test_refresh_token" == sess["user"]["refresh_token"]

    # Call the logout route
    await client.get("/logout", follow_redirects=True)
    async with client.session_transaction() as sess:
        assert "user" not in sess
