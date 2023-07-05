from flask import Blueprint

from . import MAL_ID_PREFIX, IMDB_ID_PREFIX
from .utils import respond_with

manifest_blueprint = Blueprint('manifest', __name__)

MANIFEST = {
    'id': 'com.sagetendo.mal-stremio-addon',
    'version': '0.1.0',
    'name': 'MAL-Stremio Addon',
    'description': 'MyAnimeList watchlist addon '
                   '(Requires Anime Kitsu and Torrentio to be installed if you want to watch content)',
    'types': ['anime', 'series', 'movie'],

    'catalogs': [
        {'type': 'anime', 'id': 'plan_to_watch', 'name': 'MAL: Plan To Watch'},
        {'type': 'anime', 'id': 'watching', 'name': 'MAL: Watching'},
        {'type': 'anime', 'id': 'completed', 'name': 'MAL: Completed'},
        {'type': 'anime', 'id': 'on_hold', 'name': 'MAL: On Hold'},
        {'type': 'anime', 'id': 'dropped', 'name': 'MAL: Dropped'},
        {
            'type': 'anime',
            'id': 'search_list',
            'name': 'Search Results',
            'extra': [
                {'name': 'search', 'isRequired': True}
            ]
        }
    ],

    'resources': ['catalog'],
    'idPrefixes': [MAL_ID_PREFIX, IMDB_ID_PREFIX]
}


@manifest_blueprint.route('/<token>/manifest.json')
def addon_manifest(token: str):
    """
    Provides the manifest for the addon
    :param token: The user's API token for MyAnimeList
    :return: JSON response
    """
    return respond_with(MANIFEST)
