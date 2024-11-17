import random
import urllib

import requests
from flask import Blueprint, abort, url_for, request, Request
from werkzeug.exceptions import abort

from . import mal_client, MAL_ID_PREFIX
from .manifest import MANIFEST
from .utils import respond_with, log_error
from ..db.db import UID_map_collection

catalog_bp = Blueprint('catalog', __name__)


def get_token(user_id: str):
    """
    Get the access token for the user 'user_id' from the database
    :param user_id: The user's MyAnimeList ID
    :return: The user's access token
    """
    if not (user := UID_map_collection.find_one({'uid': user_id})):
        return abort(404, 'User not found')
    return user['access_token']


def _get_transport_url(req: Request, user_id: str):
    """
    Get the transport URL for the user 'user_id'
    :param req: The request object
    :param user_id: The user's MyAnimeList ID
    :return: The transport URL
    """
    return urllib.parse.quote_plus(
        req.root_url[:-1] + url_for('manifest.addon_configured_manifest', user_id=user_id))


def _is_valid_catalog(catalog_type: str, catalog_id: str):
    """
    Check if the catalog type and id are valid
    :param catalog_type: The type of catalog to return
    :param catalog_id: The ID of the catalog to return, MAL divides a user's anime list into different categories
           (e.g. plan to watch, watching, completed, on hold, dropped)
    :return: True if the catalog type and id are valid, False otherwise
    """
    if catalog_type in MANIFEST['types']:
        for catalog in MANIFEST['catalogs']:
            if catalog['id'] == catalog_id:
                return True
    return False


def _has_genre_tag(meta: dict, genre: str = None):
    """
    Check if the meta has a genre tag
    :param meta: The meta object to check
    :param genre: The genre to filter by
    :return: True if the meta has a genre tag, False otherwise
    """
    if not genre:
        return True

    for meta_genre in meta.get('genres', []):
        if meta_genre['name'].lower() == genre.lower():
            return True
    return False


@catalog_bp.route('/<user_id>/catalog/<catalog_type>/<catalog_id>.json')
@catalog_bp.route('/<user_id>/catalog/<catalog_type>/<catalog_id>/search=<search>.json')
@catalog_bp.route('/<user_id>/catalog/<catalog_type>/<catalog_id>/skip=<offset>.json')
@catalog_bp.route('/<user_id>/catalog/<catalog_type>/<catalog_id>/genre=<genre>.json')
@catalog_bp.route('/<user_id>/catalog/<catalog_type>/<catalog_id>/genre=<genre>&search=<search>.json')
@catalog_bp.route('/<user_id>/catalog/<catalog_type>/<catalog_id>/skip=<offset>&search=<search>.json')
@catalog_bp.route(
    '/<user_id>/catalog/<catalog_type>/<catalog_id>/skip=<offset>.json&genre=<genre>&search=<search>.json')
def addon_catalog(user_id: str, catalog_type: str, catalog_id: str, offset: str = None, genre: str = None,
                  search: str = None):
    """
    Provides a list of anime from MyAnimeList
    :param user_id: The user's MyAnimeList ID
    :param catalog_type: The type of catalog to return
    :param catalog_id: The ID of the catalog to return, MAL divides a user's anime list into different categories
           (e.g. plan to watch, watching, completed, on hold, dropped)
    :param offset: The number of items to skip
    :param genre: The genre to filter by
    :param search: Used to search globally for an anime on MyAnimeList
    :return: JSON response
    """
    if not _is_valid_catalog(catalog_type, catalog_id):
        abort(404)

    token = get_token(user_id)
    field_params = 'media_type genres mean start_date end_date synopsis'
    try:
        if search:
            if len(search) < 3:
                return respond_with({'metas': []})

            response_data = mal_client.get_anime_list(token, query=search, offset=offset, fields=field_params)
        else:
            response_data = mal_client.get_user_anime_list(token, status=catalog_id, offset=offset, fields=field_params)
        unwrapped_results = [x['node'] for x in response_data.get('data', [])]

        meta_previews = []
        filtered_anime_list = filter(lambda x: _has_genre_tag(x, genre), unwrapped_results)
        for anime_item in filtered_anime_list:
            meta = _mal_to_meta(anime_item, catalog_type=catalog_type, catalog_id=catalog_id,
                                transport_url=_get_transport_url(request, user_id))
            meta_previews.append(meta)
        return respond_with({'metas': meta_previews})
    except requests.HTTPError as e:
        log_error(e)
        return respond_with({'metas': []})


def _mal_to_meta(anime_item: dict, catalog_type: str, catalog_id: str, transport_url: str):
    """
    Convert MAL anime item to a valid Stremio meta format
    :param anime_item: The MAL anime item to convert
    :param catalog_type: The type of catalog being referenced in the link meta object
    :param catalog_id: The id of catalog being referenced in the link meta object
    :param transport_url: The url to the addon's manifest.json
    :return: Stremio meta format
    """
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

    genres, links = [], []
    for genre in anime_item.get('genres', []):
        genre_name = genre['name']
        link = {'name': genre_name, 'category': 'Genres',
                'url': f"stremio:///discover/{transport_url}/{catalog_type}/{catalog_id}?genre={genre_name}"}

        links.append(link)
        genres.append(genre_name)

    if start_date := anime_item.get('start_date', None):
        start_date = start_date[:4]  # Get the year only
        start_date += '-'

        if end_date := anime_item.get('end_date', None):
            start_date += end_date[:4]

    background = None
    picture_objects = anime_item.get('pictures', [])
    if len(picture_objects) > 0:
        random_background_index = random.randint(0, len(picture_objects) - 1)
        if background := picture_objects[random_background_index].get('large', None) is None:
            background = picture_objects[random_background_index]['medium']

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
        'links': links,
        'poster': poster,
        'background': background,
        'imdbRating': mean_score,
        'releaseInfo': start_date,
        'description': synopsis
    }
