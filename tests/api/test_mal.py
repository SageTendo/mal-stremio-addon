import unittest
from unittest.mock import patch, MagicMock

from app.api.mal import (
    CLIENT_ID,
    CLIENT_SECRET,
    REDIRECT_URI,
    MyAnimeListAPI,
    TIMEOUT,
    QUERY_LIMIT,
)


class TestMyAnimeListAPI(unittest.TestCase):
    def setUp(self):
        """
        Set up the test class
        """
        self.mal_api = MyAnimeListAPI()

    def tearDown(self):
        """
        Tear down the test class
        """
        self.mal_api = None

    def test_init(self):
        """
        Test that the MyAnimeListAPI class is initialized correctly
        """
        self.assertIsNotNone(REDIRECT_URI)
        self.assertIsNotNone(CLIENT_ID)
        self.assertIsNotNone(CLIENT_SECRET)

    def test_get_auth(self):
        """
        Test that the get_auth function returns a valid auth URL
        """
        auth_url, code_verifier = self.mal_api.get_auth()
        self.assertIsNotNone(auth_url)
        self.assertIsNotNone(code_verifier)

    @patch("requests.post")
    def test_get_access_token(self, mock_post):
        """
        Test that the get_access_token function returns a valid access token
        """
        # Setup the mock response for access token
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "token_type": "bearer",
            "expires_in": 3600,
            "access_token": "new_access_token",
            "refresh_token": "refresh_token_value",
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        authorization_code = "auth_code_from_redirect"
        code_verifier = "code_verifier"
        token_details = self.mal_api.get_access_token(
            authorization_code, code_verifier=code_verifier
        )

        # Assert that the access token details are correct
        self.assertEqual(token_details["access_token"], "new_access_token")
        self.assertEqual(token_details["refresh_token"], "refresh_token_value")
        mock_post.assert_called_once_with(
            url="https://myanimelist.net/v1/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": authorization_code,
                "code_verifier": code_verifier,
                "redirect_uri": REDIRECT_URI,
            },
            timeout=TIMEOUT,
        )

    @patch("requests.post")
    def test_refresh_token(self, mock_post):
        """
        Test that the refresh_token function returns a valid access token
        """
        # Setup the mock response for refresh token
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "token_type": "bearer",
            "expires_in": 3600,
            "access_token": "new_access_token",
            "refresh_token": "refresh_token_value",
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        refresh_token = "refresh_token_value"
        token_details = self.mal_api.refresh_token(refresh_token)
        self.assertEqual(token_details["access_token"], "new_access_token")
        self.assertEqual(token_details["refresh_token"], "refresh_token_value")
        mock_post.assert_called_once_with(
            url="https://myanimelist.net/v1/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=TIMEOUT,
        )

    @patch("requests.get")
    def test_get_user_details(self, mock_get):
        """
        Test that the get_user_details function returns user details
        """
        # Setup the mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "name": "Test User",
            "picture": "https://example.com/image.jpg",
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        token = "valid_access_token"
        user_details = self.mal_api.get_user_details(token)
        self.assertEqual(user_details["id"], 123)
        self.assertEqual(user_details["name"], "Test User")
        self.assertEqual(user_details["picture"], "https://example.com/image.jpg")
        mock_get.assert_called_once_with(
            url="https://api.myanimelist.net/v1/users/@me",
            headers={"Authorization": "Bearer valid_access_token"},
            timeout=TIMEOUT,
        )

    @patch("requests.get")
    def test_get_anime_list(self, mock_get):
        """
        Test that the get_anime_list function returns a list of anime
        """
        # Setup the mock response for anime list
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": 1, "title": "Naruto", "score": 8.5},
                {"id": 2, "title": "One Piece", "score": 9.0},
                {"id": 3, "title": "Bleach", "score": 9.0},
                {"id": 4, "title": "Death Note", "score": 9.0},
                {"id": 5, "title": "Fullmetal Alchemist", "score": 9.0},
                {"id": 6, "title": "Kimetsu no Yaiba", "score": 6.0},
                {"id": 7, "title": "Naruto Shippuden", "score": 9.0},
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        token = "valid_access_token"
        anime_list = self.mal_api.get_anime_list(token, query="Naruto")

        # Assert that the anime list returned has the expected data
        self.assertEqual(len(anime_list["data"]), 7)
        self.assertEqual(anime_list["data"][0]["title"], "Naruto")
        self.assertEqual(anime_list["data"][1]["title"], "One Piece")
        mock_get.assert_called_once_with(
            url="https://api.myanimelist.net/v1/anime?q=Naruto",
            headers={"Authorization": "Bearer valid_access_token"},
            timeout=TIMEOUT,
        )

    @patch("requests.get")
    def test_get_user_anime_list(self, mock_get):
        """
        Test that the get_user_anime_list function returns a list of user's anime
        """
        # Setup the mock response for user's anime list
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": 1, "title": "Naruto", "score": 8.5},
                {"id": 2, "title": "One Piece", "score": 9.0},
                {"id": 3, "title": "Bleach", "score": 9.0},
                {"id": 4, "title": "Death Note", "score": 9.0},
                {"id": 5, "title": "Fullmetal Alchemist", "score": 9.0},
                {"id": 6, "title": "Kimetsu no Yaiba", "score": 6.0},
                {"id": 7, "title": "Naruto Shippuden", "score": 9.0},
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        token = "valid_access_token"
        user_anime_list = self.mal_api.get_user_anime_list(token)

        self.assertEqual(len(user_anime_list["data"]), 7)
        self.assertEqual(user_anime_list["data"][0]["title"], "Naruto")
        self.assertEqual(user_anime_list["data"][1]["title"], "One Piece")
        mock_get.assert_called_once_with(
            url=f"https://api.myanimelist.net/v1/users/@me/animelist?limit={QUERY_LIMIT}",
            headers={"Authorization": "Bearer valid_access_token"},
            timeout=TIMEOUT,
        )

    @patch("requests.put")
    def test_update_watched_status(self, mock_put):
        """
        Test that the update_watched_status function updates watched status
        """
        # Setup the mock response for updating watched status
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "watching",
            "num_watched_episodes": 5,
            "anime_id": 12345,
        }
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        # Assuming `token` is a valid access token
        token = "valid_access_token"
        anime_id = "12345"
        episode = 5
        updated_status = self.mal_api.update_watched_status(
            token, anime_id, episode, status="watching"
        )

        self.assertEqual(updated_status["status"], "watching")
        self.assertEqual(updated_status["num_watched_episodes"], 5)
        mock_put.assert_called_once_with(
            url="https://api.myanimelist.net/v1/anime/12345/my_list_status",
            headers={"Authorization": "Bearer valid_access_token"},
            data={"status": "watching", "num_watched_episodes": 5},
            timeout=TIMEOUT,
        )
