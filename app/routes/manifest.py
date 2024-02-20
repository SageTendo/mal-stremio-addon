from flask import Blueprint, abort

from . import MAL_ID_PREFIX
from .utils import respond_with
from ..db.db import UID_map_collection

manifest_blueprint = Blueprint('manifest', __name__)

MANIFEST = {
    'id': 'com.sagetendo.mal-stremio-addon',
    'version': '2.0.0',
    'name': 'MAL-Stremio Addon',
    'logo': 'https://i.imgur.com/zVYdffr.png',
    'description': 'Provides users with watchlist content from MyAnimeList within Stremio. '
                   'This addon only provides catalogs, with the help of AnimeKitsu',
    'types': ['anime', 'series', 'movie'],

    'catalogs': [
        {'type': 'anime', 'id': 'plan_to_watch', 'name': 'MAL: Plan To Watch', 'extra': [{'name': 'skip'}]},
        {'type': 'anime', 'id': 'watching', 'name': 'MAL: Watching', 'extra': [{'name': 'skip'}]},
        {'type': 'anime', 'id': 'completed', 'name': 'MAL: Completed', 'extra': [{'name': 'skip'}]},
        {'type': 'anime', 'id': 'on_hold', 'name': 'MAL: On Hold', 'extra': [{'name': 'skip'}]},
        {'type': 'anime', 'id': 'dropped', 'name': 'MAL: Dropped', 'extra': [{'name': 'skip'}]},
        {
            'type': 'anime',
            'id': 'search_list',
            'name': 'Search Results',
            'extra': [
                {'name': 'search', 'isRequired': True},
                {'name': 'skip'}
            ]
        }
    ],

    'resources': ['catalog', 'meta', 'subtitles'],
    'idPrefixes': [MAL_ID_PREFIX, 'kitsu']
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
