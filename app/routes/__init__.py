from app.api import LIST_STATUS
from app.api.mal import MyAnimeListAPI

mal_client = MyAnimeListAPI()

MANIFEST = {
    'id': 'com.sagetendo.mal-stremio-addon',
    'version': '1.0.0',

    'name': 'MAL Addon',
    'description': 'MyAnimeList watchlist addon',

    'types': ['anime'],

    'catalogs': [
        {
            'type': 'anime',
            'id': f'{status}',
            'name': f'MAL {status.replace("_", " ").capitalize()}',
            'extra': [{'name': 'search'}]
        } for status in LIST_STATUS
    ],

    'resources': [
        'catalog', 'meta'
    ]
}
