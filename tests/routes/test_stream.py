import unittest
from unittest.mock import patch

from run import app


class TestStream(unittest.TestCase):

    def setUp(self):
        """Set up testing client"""
        app.config['TESTING'] = True
        app.config['SECRET'] = "Testing Secret"
        self.client = app.test_client()

    @patch('app.routes.stream.get_valid_user')
    def test_fetch_streams_disabled(self, mock_user):
        """
        Test /stream endpoint with no streams
        """
        mock_user.return_value = {'fetch_streams': False}

        with self.client.session_transaction() as sess:
            sess['user'] = {'uid': '123', 'refresh_token': 'test_refresh_token'}

        response = self.client.get('123/stream/movie/mal_437.json')
        self.assertEqual(200, response.status_code)

        data = response.json
        self.assertIn('streams', data)
        self.assertEqual(0, len(data['streams']))

    @patch('app.routes.stream.get_valid_user')
    def test_fetch_streams_enabled(self, mock_user):
        """
        Test /stream endpoint
        """
        mock_user.return_value = {'fetch_streams': True}

        with self.client.session_transaction() as sess:
            sess['user'] = {'uid': '123', 'refresh_token': 'test_refresh_token'}

        response = self.client.get('123/stream/movie/mal_437.json')
        self.assertEqual(200, response.status_code)

        data = response.json
        self.assertIn('streams', data)
        self.assertNotEqual(0, len(data['streams']))
