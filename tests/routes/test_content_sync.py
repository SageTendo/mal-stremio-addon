import sys
import unittest
from unittest.mock import patch

from app.routes.content_sync import handle_current_status, handle_content_id, UpdateStatus
from run import app


class TestContentSync(unittest.TestCase):

    def setUp(self):
        """Set up testing client"""
        app.config['TESTING'] = True
        app.config['SECRET'] = "Testing Secret"
        self.test_client = app.test_client()

    def test_handle_mal_id(self):
        content_id, episode = handle_content_id("mal_12345")
        self.assertEqual("12345", content_id)
        self.assertEqual(1, episode)

    def test_handle_kitsu_id(self):
        content_id, episode = handle_content_id("kitsu:1")
        self.assertEqual(1, content_id)
        self.assertEqual(1, episode)

    def test_handle_kitsu_id_with_episode(self):
        content_id, episode = handle_content_id("kitsu:1:2")
        self.assertEqual(1, content_id)
        self.assertEqual(2, episode)

    def test_handle_no_mal_id(self):
        content_id, episode = handle_content_id(f"kitsu:{sys.maxsize}")
        self.assertEqual(None, content_id)
        self.assertEqual(-1, episode)

    def test_handle_invalid_id(self):
        content_id, episode = handle_content_id("12345")
        self.assertEqual(None, content_id)
        self.assertEqual(-1, episode)

    @patch('app.routes.mal_client.get_anime_details')
    @patch('app.routes.mal_client.update_watched_status')
    def test_addon_content_sync_valid_movie_update(self, mock_update_watched_status, mock_get_anime_details):
        # Mock responses
        mock_get_anime_details.return_value = {
            'num_episodes': 1,
            'my_list_status': {'status': 'watching', 'num_episodes_watched': 0}
        }

        # Test valid movie content ID
        response = self.test_client.get('123/subtitles/anime/kitsu:12345.json')

        self.assertEqual(200, response.status_code)
        self.assertIn('message', response.json)
        self.assertEqual(Status.OK, response.json['subtitles'][0]['lang'])

    @patch('app.routes.mal_client.get_anime_details')
    @patch('app.routes.mal_client.update_watched_status')
    @patch('app.routes.content_sync.get_valid_user')
    def test_update_untracked_anime_when_enabled(self, mock_get_user, mock_update_watched_status,
                                                 mock_get_anime_details):
        # Mock responses
        mock_get_user.return_value = {
            "uid": "123",
            "id": "123",
            "access_token": "my access token",
            "track_unlisted_anime": True
        }
        mock_get_anime_details.return_value = {
            'num_episodes': 1,
            'my_list_status': None
        }

        # Test valid movie content ID
        response = self.test_client.get('123/subtitles/anime/kitsu:12345.json')
        self.assertEqual(200, response.status_code)
        self.assertIn('message', response.json)
        self.assertEqual(UpdateStatus.OK, response.json['subtitles'][0]['lang'])

    @patch('app.routes.mal_client.get_anime_details')
    @patch('app.routes.mal_client.update_watched_status')
    @patch('app.routes.content_sync.get_valid_user')
    def test_update_untracked_anime_when_disabled(self, mock_get_user, mock_update_watched_status,
                                                  mock_get_anime_details):
        # Mock responses
        mock_get_user.return_value = {
            "uid": "123",
            "id": "123",
            "access_token": "my access token",
            "track_unlisted_anime": False
        }
        mock_get_anime_details.return_value = {
            'num_episodes': 1,
            'my_list_status': None
        }

        # Test valid movie content ID
        response = self.test_client.get('123/subtitles/anime/kitsu:12345.json')
        self.assertEqual(200, response.status_code)
        self.assertIn('message', response.json)
        self.assertEqual(Status.NOT_LIST, response.json['subtitles'][0]['lang'])

    @patch('app.routes.mal_client.get_anime_details')
    @patch('app.routes.mal_client.update_watched_status')
    def test_addon_content_sync_valid_movie_set_watched(self, mock_update_watched_status, mock_get_anime_details):
        # Mock responses
        mock_get_anime_details.return_value = {
            'num_episodes': 1,
            'my_list_status': {'status': 'watching', 'num_episodes_watched': 1}
        }

        # Test valid movie content ID
        response = self.test_client.get('123/subtitles/anime/kitsu:12345.json')

        self.assertEqual(200, response.status_code)
        self.assertIn('message', response.json)
        self.assertEqual(UpdateStatus.OK, response.json['subtitles'][0]['lang'])

    @patch('app.routes.mal_client.get_anime_details')
    @patch('app.routes.mal_client.update_watched_status')
    def test_addon_content_sync_valid_movie_no_update(self, mock_update_watched_status, mock_get_anime_details):
        # Mock responses
        mock_get_anime_details.return_value = {
            'num_episodes': 1,
            'my_list_status': {'status': 'watched', 'num_episodes_watched': 1}
        }

        # Test valid movie content ID
        response = self.test_client.get('123/subtitles/anime/kitsu:12345.json')

        self.assertEqual(200, response.status_code)
        self.assertIn('message', response.json)
        self.assertEqual(UpdateStatus.NULL, response.json['subtitles'][0]['lang'])

    @patch('app.routes.mal_client.get_anime_details')
    @patch('app.routes.mal_client.update_watched_status')
    def test_addon_content_sync_valid_series_update(self, mock_update_watched_status, mock_get_anime_details):
        # Mock responses
        mock_get_anime_details.return_value = {
            'num_episodes': 3,
            'my_list_status': {'status': 'watching', 'num_episodes_watched': 2}
        }

        # Test valid movie content ID
        response = self.test_client.get('123/subtitles/anime/kitsu:12345:3.json')

        self.assertEqual(200, response.status_code)
        self.assertIn('message', response.json)
        self.assertEqual(UpdateStatus.OK, response.json['subtitles'][0]['lang'])

    @patch('app.routes.mal_client.get_anime_details')
    @patch('app.routes.mal_client.update_watched_status')
    def test_addon_content_sync_valid_series_no_update(self, mock_update_watched_status, mock_get_anime_details):
        # Mock responses
        mock_get_anime_details.return_value = {
            'num_episodes': 3,
            'my_list_status': {'status': 'watching', 'num_episodes_watched': 2}
        }

        # Test valid movie content ID
        response = self.test_client.get('123/subtitles/anime/kitsu:12345:2.json')

        self.assertEqual(200, response.status_code)
        self.assertIn('message', response.json)
        self.assertEqual(UpdateStatus.NULL, response.json['subtitles'][0]['lang'])

    def test_handle_plan_to_watch_to_no_update(self):
        status, episode = handle_current_status("plan_to_watch", 0,
                                                0, 3)
        self.assertEqual(status, None)
        self.assertEqual(episode, -1)

    def test_handle_plan_to_watch_to_watching(self):
        status, episode = handle_current_status("plan_to_watch", 1,
                                                0, 3)
        self.assertEqual(status, "watching")
        self.assertEqual(episode, 1)

    def test_handle_plan_to_watch_to_completed(self):
        status, episode = handle_current_status("plan_to_watch", 3,
                                                2, 3)
        self.assertEqual(status, "completed")
        self.assertEqual(episode, 3)

    def test_handle_on_hold_to_watching(self):
        status, episode = handle_current_status("on_hold", 1,
                                                0, 3)
        self.assertEqual(status, "watching")
        self.assertEqual(episode, 1)

    def test_handle_on_hold_to_completed(self):
        status, episode = handle_current_status("on_hold", 3,
                                                2, 3)
        self.assertEqual(status, "completed")
        self.assertEqual(episode, 3)

    def test_handle_watching(self):
        status, episode = handle_current_status("watching", 2,
                                                1, 3)
        self.assertEqual(status, "watching")
        self.assertEqual(episode, 2)

    def test_handle_watching_to_completed(self):
        status, episode = handle_current_status("watching", 3,
                                                2, 3)
        self.assertEqual(status, "completed")
        self.assertEqual(episode, 3)
