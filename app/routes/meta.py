import requests
from flask import Blueprint, abort
from . import mal_client, MAL_ID_PREFIX
from .manifest import MANIFEST
from .utils import mal_to_meta, respond_with
from ..db.db import map_db

meta_bp = Blueprint('meta', __name__)

# Where we fetch the kitsu id of an anime based on the IMDB id. episodes based on
kitsu_API = "https://anime-kitsu.strem.fun/meta"


@meta_bp.route('/<token>/meta/<meta_type>/<meta_id>.json')
def addon_meta(token: str, meta_type: str, meta_id: str):
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
        anime_mapping = map_db.find_one({'mal_id': int(anime_id)})

        # Add IMDB id to meta item
        if anime_mapping:
            kitsu_id = None
            if 'kitsu_id' in anime_mapping.keys():
                kitsu_id = f"kitsu:{anime_mapping['kitsu_id']}"
                anime_item['kistu_id'] = kitsu_id

            # Call Kitsu Addon for Kitsu metadata
            anime_media_type = anime_item['type'] or 'anime'
            resp = requests.get(f'{kitsu_API}/{anime_media_type}/{kitsu_id}.json')

            if 200 <= resp.status_code <= 299:
                kitsu_meta = resp.json()['meta']

                # Replace mal id with kitsu id
                if 'imdb_id' in kitsu_meta.keys():
                    anime_item['imdb_id'] = kitsu_meta['imdb_id']

                # Check for logo and add it to meta
                if 'logo' in kitsu_meta.keys():
                    anime_item['logo'] = kitsu_meta['logo']

                # Add videos to kitsu if they exist
                if 'videos' in kitsu_meta.keys():
                    anime_item['videos'] = kitsu_meta['videos']
    return respond_with({'meta': anime_item})  # Return with CORS to client
