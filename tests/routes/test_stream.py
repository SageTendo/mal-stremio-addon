import unittest

from run import app


class TestStream(unittest.TestCase):

    def setUp(self):
        """Set up testing client"""
        app.config['TESTING'] = True
        app.config['SECRET'] = "Testing Secret"
        self.client = app.test_client()

    def test_fetch_streams_disabled(self):
        """
        Test /stream endpoint with no streams
        """
        response = self.client.get('123/stream/movie/mal_437.json')
        self.assertEqual(200, response.status_code)

        data = response.json
        self.assertIn('streams', data)
        self.assertEqual(0, len(data['streams']))

    def test_fetch_streams_enabled(self):
        """
        Test /stream endpoint
        """
        with self.client.session_transaction() as sess:
            sess['user'] = {'uid': '123',
                            'id': '123',
                            'name': 'Test User',
                            'access_token': 'test_access_token',
                            'refresh_token': 'test_refresh_token',
                            'expires_in': 3600}

        with self.client as client:
            client.post('/configure', data={'fetch_streams': 'true'})
            response = client.get('123/stream/movie/mal_437.json')
            self.assertEqual(200, response.status_code)

            data = response.json
            self.assertIn('streams', data)
            self.assertNotEqual(0, len(data['streams']))
