import imdb
from flask import Blueprint, abort
from . import mal_client, MANIFEST
from .utils import mal_to_meta, respond_with

meta_bp = Blueprint('meta', __name__)

imdb_client = imdb.Cinemagoer(accessSystem='http')


@meta_bp.route('/<token>/meta/<meta_type>/<meta_id>.json')
def addon_meta(token: str, meta_type: str, meta_id: str):
    # Check if meta type exists in manifest
    if meta_type not in MANIFEST['types']:
        abort(404)

    # Fetch anime details from MAL
    anime_id = meta_id.replace('mal-', '')  # Extract anime id from addon meta id
    field_params = 'media_type genres mean start_date end_date synopsis pictures'  # Additional fields to return
    anime_item = mal_client.get_anime_details(token, anime_id, fields=field_params)

    if anime_item:
        # Format the details to a meta format
        anime_item = mal_to_meta(anime_item, meta_type)

        # Search for anime on IMDB
        imdb_items = imdb_client.search_movie_advanced(title=anime_item['name'], adult=True, results=5)

        # Add IMDB id to meta item
        if imdb_items:
            anime_item['imdb_id'] = f"tt{imdb_items[0].getID()}"
    return respond_with({'meta': anime_item})  # Return with CORS to client
