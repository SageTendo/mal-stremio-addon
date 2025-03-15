import unittest

from run import app


class TestStream(unittest.TestCase):

    def setUp(self):
        """Set up testing client"""
        app.config['TESTING'] = True
        app.config['SECRET'] = "Testing Secret"
        self.client = app.test_client()

    def test_addon_stream(self):
        """
        Test /stream endpoint with no streams
        """
        response = self.client.get('123/fetch_streams=false/stream/movie/mal_437.json')
        self.assertEqual(200, response.status_code)

        data = response.json
        self.assertIn('streams', data)
        self.assertEqual(0, len(data['streams']))

    def test_disable_streams(self):
        """
        Test /stream endpoint
        """
        response = self.client.get('123/fetch_streams=true/stream/movie/mal_437.json')
        self.assertEqual(200, response.status_code)

        data = response.json
        self.assertIn('streams', data)
        self.assertNotEqual(0, len(data['streams']))
