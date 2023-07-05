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
    anime_details = mal_client.get_anime_details(token, anime_id, fields=field_params)

    # Check if anime details exist
    if not anime_details:
        return respond_with({'meta': None})

    # Format the details to stremio's meta format
    anime_details = mal_to_meta(anime_details)

    # Fetch kitsu id from map db
    anime_mapping = anime_map_collection.find_one({'mal_id': int(anime_id)})

    # Add kitsu metadata to anime details
    if anime_mapping:
        if (kitsu_id := anime_mapping.get('kitsu_id', None)) is None:
            return respond_with({'meta': anime_details})

        # Format kitsu id and add to meta
        formated_kitsu_id = f'kitsu:{kitsu_id}'
        anime_details['kitsu_id'] = formated_kitsu_id

        # Call Kitsu Addon for Kitsu metadata
        anime_media_type = anime_details.get('type', 'anime')
        resp = requests.get(f'{kitsu_API}/{anime_media_type}/{formated_kitsu_id}.json')
        if 200 <= resp.status_code <= 299:
            kitsu_meta = resp.json().get('meta')

            # add imdb id to meta
            imdb_id = kitsu_meta.get('imdb_id')
            if imdb_id:
                anime_details['imdb_id'] = imdb_id

            # Check for logo and add it to meta
            logo = kitsu_meta.get('logo')
            if logo:
                anime_details['logo'] = logo

            # Add videos to kitsu if they exist
            videos = kitsu_meta.get('videos')
            if videos:
                anime_details['videos'] = videos

            # Add links to kitsu if they exist
            links = kitsu_meta.get('links')
            if links:
                anime_details['links'] = links
        else:
            print("FETCH ERROR: Failed to call Kitsu API")
    return respond_with({'meta': anime_details})  # Return with CORS to client
