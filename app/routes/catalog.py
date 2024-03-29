import random

from flask import Blueprint, abort
from werkzeug.exceptions import abort

from . import mal_client, MAL_ID_PREFIX
from .manifest import MANIFEST
from .utils import respond_with
from ..db.db import UID_map_collection

catalog_bp = Blueprint('catalog', __name__)


def get_token(user_id: str):
    if not (user := UID_map_collection.find_one({'uid': user_id})):
        return abort(404, 'User not found')
    return user['access_token']


@catalog_bp.route('/<user_id>/catalog/<catalog_type>/<catalog_id>.json')
@catalog_bp.route('/<user_id>/catalog/<catalog_type>/<catalog_id>/skip=<offset>.json')
def addon_catalog(user_id: str, catalog_type: str, catalog_id: str, offset: str = None):
    """
    Provides a list of anime from MyAnimeList
    :param user_id: The user's MyAnimeList ID
    :param catalog_type: The type of catalog to return
    :param catalog_id: The ID of the catalog to return, MAL divides a user's anime list into different categories
           (e.g. plan to watch, watching, completed, on hold, dropped)
    :param offset: The number of items to skip
    :return: JSON response
    """
    if catalog_type not in MANIFEST['types']:
        abort(404)

    # Check if catalog exists in manifest
    catalog_exists = False
    for catalog in MANIFEST['catalogs']:
        if catalog_id == catalog['id']:
            catalog_exists = True

    if not catalog_exists:
        abort(404)

    token = get_token(user_id)

    field_params = 'media_type genres mean start_date end_date synopsis'  # Additional fields to return
    response_data = mal_client.get_user_anime_list(token, status=catalog_id, offset=offset, fields=field_params)
    response_data = response_data['data']  # Get array of node objects

    meta_previews = []
    for data_item in response_data:
        anime_item = data_item['node']

        # Convert to Stremio compatible JSON
        meta = mal_to_meta(anime_item)
        meta_previews.append(meta)
    return respond_with({'metas': meta_previews})


@catalog_bp.route('/<user_id>/catalog/<catalog_type>/<catalog_id>/search=<search_query>.json')
def search_metas(user_id: str, catalog_type: str, catalog_id: str, search_query: str):
    """
    Provides a list of anime from MyAnimeList based on a search query
    :param user_id: The user's MyAnimeList ID
    :param catalog_type: The type of catalog to return
    :param catalog_id: The ID of the catalog to return, MAL divides a user's anime list into different categories
           (e.g. plan to watch, watching, completed, on hold, dropped)
    :param search_query: The search query
    :return: JSON response
    """
    if catalog_type not in MANIFEST['types']:
        abort(404)

    # Check if catalog exists in manifest
    catalog_exists = False
    for catalog in MANIFEST['catalogs']:
        if catalog_id == catalog['id']:
            catalog_exists = True

    if not catalog_exists:
        abort(404)

    token = get_token(user_id)

    field_params = 'media_type alternative_titles'  # Additional fields to return
    response = mal_client.get_anime_list(token, query=search_query, fields=field_params)
    response_data: list = response['data']  # Get array of node objects

    meta_previews = []
    for data_item in response_data:
        anime_item = data_item['node']

        # Convert to Stremio compatible JSON
        meta = mal_to_meta(anime_item)
        meta_previews.append(meta)
    return respond_with({'metas': meta_previews})


def mal_to_meta(anime_item: dict):
    """
    Convert MAL anime item to a valid Stremio meta format
    :param anime_item: The MAL anime item to convert
    :return: Stremio meta format
    """
    # Metadata stuff
    formatted_content_id = None
    if content_id := anime_item.get('id', None):
        formatted_content_id = f"{MAL_ID_PREFIX}_{content_id}"

    title = anime_item.get('title', None)
    mean_score = anime_item.get('mean', None)
    synopsis = anime_item.get('synopsis', None)

    poster = None
    if poster_objects := anime_item.get('main_picture', {}):
        if poster := poster_objects.get('large', None):
            poster = poster_objects.get('medium')

    if genres := anime_item.get('genres', {}):
        genres = [genre['name'] for genre in genres]

    # Check for release info and format it if it exists
    if start_date := anime_item.get('start_date', None):
        start_date = start_date[:4]  # Get the year only
        start_date += '-'

        if end_date := anime_item.get('end_date', None):
            start_date += end_date[:4]

    # Check for background key in anime_item
    background = None
    picture_objects = anime_item.get('pictures', [])
    if len(picture_objects) > 0:
        random_background_index = random.randint(0, len(picture_objects) - 1)
        if background := picture_objects[random_background_index].get('large', None) is None:
            background = picture_objects[random_background_index]['medium']

    # Check for media type and filter out non series and movie types
    if media_type := anime_item.get('media_type', None):
        if media_type in ['ona', 'ova', 'special', 'tv', 'unknown']:
            media_type = 'series'
        elif media_type != 'movie':
            media_type = None

    return {
        'cacheMaxAge': 43200,
        'staleRevalidate': 3600,
        'staleError': 3600,
        'id': formatted_content_id,
        'name': title,
        'type': media_type,
        'genres': genres,
        'poster': poster,
        'background': background,
        'imdbRating': mean_score,
        'releaseInfo': start_date,
        'description': synopsis
    }
