import unittest
from unittest.mock import patch

from run import app

DUMMY_MAL_RESPONSE = {'data': [
    {'node': {'id': 1,
              'title': 'Naruto',
              'mean': 8.5,
              'synopsis': 'Naruto anime',
              'main_picture': {'large': 'http://example.com/poster.jpg'},
              'pictures': [{'large': 'http://example.com/poster1.jpg'},
                           {'large': 'http://example.com/poster2.jpg'},
                           {'large': 'http://example.com/poster3.jpg'}],
              'genres': [{'name': 'Action'}],
              'start_date': '2002-02-15',
              'end_date': '2002-02-15',
              'media_type': 'tv'}
     },
    {'node': {'id': 2,
              'title': 'Naruto Shippuden',
              'mean': 8.5,
              'synopsis': 'Naruto Shippuden anime',
              'main_picture': {'large': 'http://example.com/poster.jpg'},
              'pictures': [{'large': 'http://example.com/poster1.jpg'},
                           {'medium': 'http://example.com/poster2.jpg'},
                           {'large': 'http://example.com/poster3.jpg'}],
              'genres': [{'name': 'Action'}],
              'start_date': '2002-02-15',
              'end_date': '2002-02-15',
              'media_type': 'ova'}
     },
    {'node': {'id': 3,
              'title': 'Naruto Shippuden',
              'mean': 8.5,
              'synopsis': 'Naruto Shippuden anime',
              'main_picture': {'large': 'http://example.com/poster.jpg'},
              'pictures': [{'large': 'http://example.com/poster1.jpg'}],
              'genres': [{'name': 'Action'}],
              'start_date': None,
              'end_date': None,
              'media_type': 'movie'}
     },
    {'node': {'id': 4,
              'title': 'Naruto Shippuden',
              'mean': 8.5,
              'synopsis': 'Naruto Shippuden anime',
              'main_picture': {'large': 'http://example.com/poster.jpg'},
              'pictures': [{'medium': 'http://example.com/poster2.jpg'}],
              'genres': [{'name': 'Action'}],
              'start_date': '2002-02-15',
              'end_date': '2002-02-15',
              'media_type': 'special'}
     },
    {'node': {'id': 5,
              'title': 'Naruto Shippuden',
              'mean': None,
              'synopsis': 'Naruto Shippuden anime',
              'main_picture': {'medium': 'http://example.com/poster.jpg'},
              'pictures': [{'large': 'http://example.com/poster3.jpg'}],
              'genres': [{'name': 'Action'}],
              'start_date': '2002-02-15',
              'end_date': None,
              'media_type': 'unknown'}
     },
    {'node': {'id': 6,
              'title': 'Naruto Shippuden',
              'mean': 8.5,
              'synopsis': 'Naruto Shippuden anime',
              'main_picture': {'large': 'http://example.com/poster.jpg'},
              'pictures': [{'large': 'http://example.com/poster1.jpg'}],
              'genres': [{'name': 'Action'}],
              'start_date': '2002-02-15',
              'end_date': '2002-02-15',
              'media_type': 'movie'}
     }
]}


class TestCatalog(unittest.TestCase):
    def setUp(self):
        """Set up the Flask test client."""
        self.client = app.test_client()

    def _meta_asserts(self, response_data):
        self.assertIn('metas', response_data)
        for anime in response_data['metas']:
            self.assertIn('id', anime)
            self.assertIn('mal_', anime['id'])
            self.assertIn('name', anime)
            self.assertIsNotNone(anime['name'])

            self.assertIn('type', anime)
            self.assertIn(anime['type'], ['series', 'movie'])
            self.assertIn('genres', anime)
            self.assertIsNotNone(anime['genres'])

            self.assertIn('links', anime)
            self.assertEqual(anime['links'][0]['name'], 'Action')
            self.assertIsNotNone(anime['links'][0]['url'])

            self.assertIn('poster', anime)
            self.assertEqual(anime['poster'], 'http://example.com/poster.jpg')
            self.assertIn('imdbRating', anime)
            self.assertIn(anime['imdbRating'], ['8.5', None])

            self.assertIn('background', anime)
            self.assertIn(anime['background'], ['http://example.com/poster1.jpg',
                                                'http://example.com/poster2.jpg', 'http://example.com/poster3.jpg'])

            self.assertIn('releaseInfo', anime)
            self.assertIn(anime['releaseInfo'], ['2002-', '2002-2002', None])
            self.assertIn('description', anime)
            self.assertIn(anime['description'], ['Naruto anime', 'Naruto Shippuden anime', None])

    @patch('app.routes.mal_client.get_user_anime_list')
    @patch('app.routes.mal_client.get_anime_list')
    def test_catalog(self, mock_get_user_anime_list, mock_get_anime_list):
        """Test valid catalog request."""
        mock_get_user_anime_list.return_value = DUMMY_MAL_RESPONSE
        mock_get_anime_list.return_value = DUMMY_MAL_RESPONSE

        response = self.client.get('/123/catalog/anime/watching.json')
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self._meta_asserts(response_data)

    @patch('app.routes.mal_client.get_anime_list')
    def test_search(self, mock_get_anime_list):
        """Test catalog request with a search query."""
        mock_get_anime_list.return_value = DUMMY_MAL_RESPONSE

        response = self.client.get('/123/catalog/anime/search_list/search=Naruto.json')
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        assert len(response_data['metas']) > 0
        self._meta_asserts(response_data)

        # Test bad request
        response = self.client.get('/123/catalog/anime/search_list/search=N.json')
        self.assertEqual(response.status_code, 400)

    @patch('app.routes.mal_client.get_user_anime_list')
    def test_genre_filtering_no_results(self, mock_get_user_anime_list):
        """Test catalog request with a search query."""
        mock_get_user_anime_list.return_value = DUMMY_MAL_RESPONSE

        response = self.client.get('/123/catalog/anime/watching/genre=Adventure.json')
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertListEqual(response_data['metas'], [])

    @patch('app.routes.mal_client.get_user_anime_list')
    def test_genre_filtering(self, mock_get_user_anime_list):
        """Test catalog request with a search query."""
        mock_get_user_anime_list.return_value = DUMMY_MAL_RESPONSE

        response = self.client.get('/123/catalog/anime/watching/genre=Action.json')
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        assert len(response_data['metas']) > 0
        self._meta_asserts(response_data)

        response = self.client.get('/123/catalog/anime/watching/genre=Boys Love.json')
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        assert len(response_data['metas']) == 0
        self._meta_asserts(response_data)

        response = self.client.get("/123/catalog/anime/watching/genre={'id':%201,%20'name':%20'Action'}.json")
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        assert len(response_data['metas']) > 0
        self._meta_asserts(response_data)
