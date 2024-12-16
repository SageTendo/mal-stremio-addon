import unittest

from run import app


class TestStreamBlueprint(unittest.TestCase):

    def setUp(self):
        """Set up testing client"""
        self.client = app.test_client()

    def test_addon_stream(self):
        """
        Test /stream endpoint
        """
        response = self.client.get('123/stream/movie/mal_437.json')
        self.assertEqual(response.status_code, 200)

        data = response.json
        self.assertIn('streams', data)
