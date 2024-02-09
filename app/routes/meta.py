import logging

import requests
from flask import Blueprint, abort

from . import IMDB_ID_PREFIX
from .manifest import MANIFEST
from .utils import respond_with

meta_bp = Blueprint('meta', __name__)

kitsu_API = "https://anime-kitsu.strem.fun/meta"


@meta_bp.route('/<user_id>/meta/<meta_type>/<meta_id>.json')
def addon_meta(user_id: str, meta_type: str, meta_id: str):
    """
    Provides metadata for a specific content
    :param user_id: The user's API token for MyAnimeList
    :param meta_type: The type of metadata to return
    :param meta_id: The ID of the content
    :return: JSON response
    """
    # ignore imdb ids for older versions of mal-stremio
    if IMDB_ID_PREFIX in meta_id:
        return {}

    # Check if meta type exists in manifest
    if meta_type not in MANIFEST['types']:
        abort(404)

    resp = requests.get(f"{kitsu_API}/{meta_type}/{meta_id.replace('_', ':')}.json")
    if not resp.ok:
        logging.error(resp.status_code, resp.reason)
        abort(404, f"{resp.status_code}: {resp.reason}")

    return respond_with(resp.json())  # Return with CORS to client
