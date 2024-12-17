import sys
import unittest
from unittest.mock import patch, MagicMock

from app.routes.content_sync import handle_current_status, _handle_content_id
from run import app


class TestContentSync(unittest.TestCase):

    def setUp(self):
        """Set up testing client"""
        self.test_client = app.test_client()

    def test_handle_mal_id(self):
        content_id, episode = _handle_content_id("mal_12345")
        self.assertEqual(content_id, "12345")
        self.assertEqual(episode, 1)

    def test_handle_kitsu_id(self):
        content_id, episode = _handle_content_id("kitsu:1")
        self.assertEqual(content_id, 1)
        self.assertEqual(episode, 1)

    def test_handle_kitsu_id_with_episode(self):
        content_id, episode = _handle_content_id("kitsu:1:2")
        self.assertEqual(content_id, 1)
        self.assertEqual(episode, 2)

    def test_handle_no_mal_id(self):
        content_id, episode = _handle_content_id(f"kitsu:{sys.maxsize}")
        self.assertEqual(content_id, None)
        self.assertEqual(episode, -1)

    def test_handle_invalid_id(self):
        content_id, episode = _handle_content_id("12345")
        self.assertEqual(content_id, None)
        self.assertEqual(episode, -1)

    @patch('app.routes.mal_client.get_anime_details')
    @patch('app.routes.mal_client.update_watched_status')
    def test_addon_content_sync_valid_movie_update(self, mock_update_watched_status, mock_get_anime_details):
        # Mock responses
        mock_get_anime_details.return_value = {
            'num_episodes': 1,
            'my_list_status': {'status': 'watching', 'num_episodes_watched': 0}
        }
        mock_update_watched_status.status_code = 200

        # Test valid movie content ID
        response = self.test_client.get('/123/subtitles/anime/kitsu:12345.json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Updated watched status')

    @patch('app.routes.mal_client.get_anime_details')
    @patch('app.routes.mal_client.update_watched_status')
    def test_addon_content_sync_valid_movie_no_update(self, mock_update_watched_status, mock_get_anime_details):
        # Mock responses
        mock_get_anime_details.return_value = {
            'num_episodes': 1,
            'my_list_status': {'status': 'watching', 'num_episodes_watched': 1}
        }
        mock_update_watched_status.status_code = 200

        # Test valid movie content ID
        response = self.test_client.get('/123/subtitles/anime/kitsu:12345.json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Updated watched status')

    @patch('app.routes.mal_client.get_anime_details')
    @patch('app.routes.mal_client.update_watched_status')
    def test_addon_content_sync_valid_series_update(self, mock_update_watched_status, mock_get_anime_details):
        # Mock responses
        mock_get_anime_details.return_value = {
            'num_episodes': 3,
            'my_list_status': {'status': 'watching', 'num_episodes_watched': 2}
        }
        mock_update_watched_status.status_code = 200

        # Test valid movie content ID
        response = self.test_client.get('/123/subtitles/anime/kitsu:12345:3.json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Updated watched status')

    @patch('app.routes.mal_client.get_anime_details')
    @patch('app.routes.mal_client.update_watched_status')
    def test_addon_content_sync_valid_series_no_update(self, mock_update_watched_status, mock_get_anime_details):
        # Mock responses
        mock_get_anime_details.return_value = {
            'num_episodes': 3,
            'my_list_status': {'status': 'watching', 'num_episodes_watched': 2}
        }
        mock_update_watched_status.status_code = 200

        # Test valid movie content ID
        response = self.test_client.get('/123/subtitles/anime/kitsu:12345:2.json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Nothing to update')

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