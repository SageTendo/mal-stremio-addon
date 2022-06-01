from flask import Blueprint, request
from werkzeug.exceptions import abort

from . import MANIFEST, mal_client
from .utils import respond_with, mal_to_meta

catalog_bp = Blueprint('catalog', __name__)


@catalog_bp.route('/<token>/catalog/<catalog_type>/<catalog_id>.json')
@catalog_bp.route('/<token>/catalog/<catalog_type>/<catalog_id>/<offset>.json')
def addon_catalog(token: str, catalog_type: str, catalog_id: str, offset: str = None):
    if catalog_type not in MANIFEST['types']:
        abort(404)

    catalog_exists = False
    for catalog in MANIFEST['catalogs']:
        if catalog_id == catalog['id']:
            catalog_exists = True

    if not catalog_exists:
        abort(404)

    # Get offset value if exists (from 'skip=#')
    if offset:
        _, offset = offset.split('=')

    field_params = 'media_type genres mean start_date end_date synopsis'  # Additional fields to return
    response_data = mal_client.get_user_anime_list(token, status=catalog_id, offset=offset, fields=field_params)
    response_data = response_data['data']  # Get array of node objects

    meta_previews = []
    for data_item in response_data:
        anime_item = data_item['node']

        # Metadata stuff
        meta = mal_to_meta(anime_item)
        meta_previews.append(meta)
    return respond_with({'metas': meta_previews})
