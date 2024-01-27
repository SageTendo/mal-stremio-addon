from flask import Blueprint, abort

from . import MAL_ID_PREFIX, IMDB_ID_PREFIX
from .utils import respond_with
from ..db.db import UID_map_collection

manifest_blueprint = Blueprint('manifest', __name__)

MANIFEST = {
    'id': 'com.sagetendo.mal-stremio-addon',
    'version': '1.1.0',
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

    'resources': ['catalog', 'meta'],
    'idPrefixes': [MAL_ID_PREFIX, IMDB_ID_PREFIX]
}


@manifest_blueprint.route('/<user_id>/manifest.json')
def addon_manifest(user_id: str):
    """
    Provides the manifest for the addon
    :param user_id: The user's MyAnimeList ID
    :return: JSON response
    """

    user = UID_map_collection.find_one({'uid': user_id})
    if not user:
        return abort(404, f'User ID: {user_id} not found')

    return respond_with(MANIFEST)
