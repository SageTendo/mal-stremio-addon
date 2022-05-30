import random

from flask import Blueprint, abort
from . import mal_client, MANIFEST
from .utils import mal_to_meta, respond_with

meta_bp = Blueprint('meta', __name__)


@meta_bp.route('/<token>/meta/<meta_type>/<meta_id>.json')
def addon_meta(token: str, meta_type: str, meta_id: str):
    # Check if meta type exists in manifest
    if meta_type not in MANIFEST['types']:
        abort(404)

    # Fetch anime details from MAL
    anime_id = meta_id.replace('mal-', '')  # Extract anime id from addon meta id
    field_params = 'genres mean start_date end_date synopsis pictures'  # Additional fields to return

    anime_item = mal_client.get_anime_details(token, anime_id, fields=field_params)

    # Format the details to a meta format
    anime_item = mal_to_meta(anime_item, meta_type)
    # TODO

    # Return with CORS to client
    return respond_with({'meta': anime_item})
