import datetime
import time

import requests
from flask import Blueprint, abort
from . import mal_client, MAL_ID_PREFIX
from .manifest import MANIFEST
from .utils import mal_to_meta, respond_with
from ..db.db import map_db

meta = Blueprint('meta', __name__)

# Where we fetch the kitsu id of an anime based on the IMDB id. episodes based on
kitsu_API = "https://anime-kitsu.strem.fun/meta"


@meta.route('/<token>/meta/<meta_type>/<meta_id>.json')
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
            kitsu_id = f'kitsu:{anime_mapping.get("kitsu_id")}'
            if kitsu_id:
                anime_item['kistu_id'] = kitsu_id

            # Call Kitsu Addon for Kitsu metadata
            anime_media_type = anime_item.get('type', 'anime')
            resp = requests.get(f'{kitsu_API}/{anime_media_type}/{kitsu_id}.json')

            if 200 <= resp.status_code <= 299:
                kitsu_meta = resp.json().get('meta')

                # Replace mal id with kitsu id
                imdb_id = kitsu_meta.get('imdb_id')
                if imdb_id:
                    anime_item['imdb_id'] = imdb_id

                # Check for logo and add it to meta
                logo = kitsu_meta.get('logo')
                if logo:
                    anime_item['logo'] = logo

                # Add videos to kitsu if they exist
                videos = kitsu_meta.get('videos')
                if videos:
                    anime_item['videos'] = videos
            else:
                print("FETCH ERROR: Failed to call Kitsu API")
    return respond_with({'meta': anime_item})  # Return with CORS to client
