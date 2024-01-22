from flask import Blueprint
from werkzeug.exceptions import abort

from . import mal_client
from .manifest import MANIFEST
from .utils import respond_with, mal_to_meta, get_token

catalog_bp = Blueprint('catalog', __name__)


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
