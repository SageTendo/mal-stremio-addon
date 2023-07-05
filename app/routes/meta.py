import requests
from flask import Blueprint, abort

from . import mal_client, MAL_ID_PREFIX
from .manifest import MANIFEST
from .utils import mal_to_meta, respond_with
from ..db.db import anime_map_collection

meta = Blueprint('meta', __name__)

# Kitsu API to get anime metadata
kitsu_API = "https://anime-kitsu.strem.fun/meta"


@meta.route('/<token>/meta/<meta_type>/<meta_id>.json')
def addon_meta(token: str, meta_type: str, meta_id: str):
    """
    Provides metadata for a specific content
    :param token: The user's API token for MyAnimeList
    :param meta_type: The type of metadata to return
    :param meta_id: The ID of the content
    :return: JSON response
    """
    # Check if meta type exists in manifest
    if meta_type not in MANIFEST['types']:
        abort(404)

    # Fetch anime details from MAL
    anime_id = meta_id.replace(MAL_ID_PREFIX, '')  # Extract anime id from addon meta id
    field_params = 'media_type genres mean start_date end_date synopsis pictures'  # Additional fields to return
    anime_item = mal_client.get_anime_details(token, anime_id, fields=field_params)

    if anime_item:
        # Format the details to a meta format
        anime_item = mal_to_meta(anime_item)

        # Fetch kitsu id from map db
        anime_mapping = anime_map_collection.find_one({'mal_id': int(anime_id)})

        # Add IMDB id to meta item
        if anime_mapping:
            if kitsu_id := anime_mapping.get("kitsu_id") is not None:
                anime_item['kitsu_id'] = f'kitsu:{kitsu_id}'
    return respond_with({'meta': anime_item})  # Return with CORS to client
