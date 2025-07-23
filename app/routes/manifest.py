from flask import Blueprint

import config
from . import MAL_ID_PREFIX
from .utils import respond_with
from ..db.db import get_user

manifest_blueprint = Blueprint('manifest', __name__)

genres = ['Action', 'Adventure', 'Avant Garde',
          'Award Winning', 'Boys Love', 'Comedy',
          'Drama', 'Fantasy', 'Girls Love', 'Gourmet',
          'Horror', 'Mystery', 'Romance', 'Sci-Fi',
          'Slice of Life', 'Sports', 'Supernatural',
          'Ecchi', 'Hentai', 'Erotica']

MANIFEST = {
    'id': 'com.sagetendo.mal-stremio-addon',
    'version': '3.2.0',
    'name': 'MAL-Stremio Addon',
    'logo': 'https://i.imgur.com/zVYdffr.png',
    'description': 'Provides users with watchlist content from MyAnimeList within Stremio. '
                   'This addon only provides catalogs, with the help of AnimeKitsu',
    'types': ['anime', 'series', 'movie'],

    'catalogs': [
        {'type': 'anime', 'id': 'plan_to_watch', 'name': 'MAL: Plan To Watch',
         'extra': [{'name': 'skip'},
                   {'name': 'genre', 'options': genres}],
         'genre': genres},
        {
            'type': 'anime', 'id': 'watching', 'name': 'MAL: Watching',
            'extra': [{'name': 'skip'},
                      {'name': 'genre', 'options': genres}],
            'genre': genres
        },
        {'type': 'anime', 'id': 'completed', 'name': 'MAL: Completed',
         'extra': [{'name': 'skip'},
                   {'name': 'genre', 'options': genres}],
         'genre': genres
         },
        {'type': 'anime', 'id': 'on_hold', 'name': 'MAL: On Hold',
         'extra': [{'name': 'skip'},
                   {'name': 'genre', 'options': genres}],
         'genre': genres
         },
        {'type': 'anime', 'id': 'dropped', 'name': 'MAL: Dropped',
         'extra': [{'name': 'skip'},
                   {'name': 'genre', 'options': genres}],
         'genre': genres
         },
        {
            'type': 'anime',
            'id': 'search_list',
            'name': 'MAL',
            'extra': [
                {'name': 'search', 'isRequired': True},
                {'name': 'skip'},
                {'name': 'genre', 'options': genres, 'isRequired': False}
            ],
            'genre': genres
        }
    ],

    'behaviorHints': {'configurable': True},
    'resources': ['catalog', 'meta', 'subtitles', 'stream'],
    'idPrefixes': [MAL_ID_PREFIX, 'kitsu']
}


@manifest_blueprint.route('/manifest.json')
def addon_unconfigured_manifest():
    """
    Provides the initial manifest for the addon before the user has authenticated with MyAnimeList
    The user is required to configure the addon before they can use it
    :return: JSON response
    """
    unconfigured_manifest: dict = MANIFEST.copy()
    unconfigured_manifest['behaviorHints'] = {
        'configurable': True,
        'configurationRequired': True
    }
    return respond_with(unconfigured_manifest, cacheMaxAge=config.MANIFEST_CACHE_DURATION, stale_revalidate=300)


@manifest_blueprint.route('/<user_id>/manifest.json')
def addon_configured_manifest(user_id: str):
    """
    Provides the manifest for the addon after the user has authenticated with MyAnimeList
    :param user_id: The user's MyAnimeList ID
    :return: JSON response
    """
    user = get_user(user_id)
    if not user:
        return respond_with({"error": f'User ID: {user_id} not found'}, private=True, cacheMaxAge=1800)
    return respond_with(MANIFEST, cacheMaxAge=config.MANIFEST_CACHE_DURATION, stale_revalidate=300)
