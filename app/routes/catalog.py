from flask import Blueprint
from werkzeug.exceptions import abort

from . import MANIFEST, mal_client
from .utils import respond_with

catalog_bp = Blueprint('catalog', __name__)


@catalog_bp.route('/<token>/catalog/<catalog_type>/<catalog_id>.json')
def addon_catalog(token: str, catalog_type: str, catalog_id: str):
    if catalog_type not in MANIFEST['types']:
        abort(404)

    catalog_exists = False
    for catalog in MANIFEST['catalogs']:
        if catalog_id == catalog['id']:
            catalog_exists = True

    if not catalog_exists:
        abort(404)

    field_params = 'genres mean start_date end_date synopsis'  # Additional fields to return
    response_data = mal_client.get_user_anime_list(token, status=catalog_id, fields=field_params)
    response_data = response_data['data']  # Get array of node objects

    meta_previews = {'metas': []}
    for data_item in response_data:
        anime_item = data_item['node']

        # Metadata stuff
        posters = anime_item['main_picture']
        medium_poster = posters['medium']
        # large_poster = posters['large']
        genres = [genre['name'] for genre in anime_item['genres']]
        rating = anime_item['mean']
        start_date = anime_item['start_date'][:4]  # Get the year only
        description = anime_item['synopsis']

        # Format start date if end_date of airing was returned
        if not anime_item['end_date']:
            start_date += '-'

        meta_previews['metas'].append({
            'id': f"tt{anime_item['id']}",
            'type': catalog_type,
            'name': anime_item['title'],
            'genres': genres,
            'poster': medium_poster,
            'imdbRating': rating,
            'releaseInfo': start_date,
            'description': description
        })
    return respond_with(meta_previews)
