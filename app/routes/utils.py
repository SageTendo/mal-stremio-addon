import random

from flask import jsonify, abort

from app.db.db import UID_map_collection
from app.routes import MAL_ID_PREFIX


# Enable CORS
def respond_with(data):
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = "*"
    resp.headers['Access-Control-Allow-Headers'] = '*'
    return resp


def get_token(user_id: str):
    user = UID_map_collection.find_one({'uid': user_id})
    if not user:
        return abort(404, 'User not found')

    return user['access_token']


def mal_to_meta(anime_item: dict):
    """
    Convert MAL anime item to a Stremio's meta format
    :param anime_item: The MAL anime item to convert
    :return: Stremio's meta format
    """
    # Metadata stuff
    formatted_content_id = None
    if content_id := anime_item.get('id', None):
        formatted_content_id = f"{MAL_ID_PREFIX}_{content_id}"

    title = anime_item.get('title', None)
    mean_score = anime_item.get('mean', None)
    synopsis = anime_item.get('synopsis', None)

    poster = None
    if poster_objects := anime_item.get('main_picture', {}):
        if poster := poster_objects.get('large', None):
            poster = poster_objects.get('medium')

    if genres := anime_item.get('genres', {}):
        genres = [genre['name'] for genre in genres]

    # Check for release info and format it if it exists
    if start_date := anime_item.get('start_date', None):
        start_date = start_date[:4]  # Get the year only
        start_date += '-'

        if end_date := anime_item.get('end_date', None):
            start_date += end_date

    # Check for background key in anime_item
    background = None
    picture_objects = anime_item.get('pictures', [])
    if len(picture_objects) > 0:
        random_background_index = random.randint(0, len(picture_objects) - 1)
        if background := picture_objects[random_background_index].get('large', None) is None:
            background = picture_objects[random_background_index]['medium']

    # Check for media type and filter out non series and movie types
    if media_type := anime_item.get('media_type', None):
        if media_type in ['ona', 'ova', 'special', 'tv', 'unknown']:
            media_type = 'series'
        elif media_type != 'movie':
            media_type = None

    return {
        'id': formatted_content_id,
        'name': title,
        'type': media_type,
        'genres': genres,
        'poster': poster,
        'background': background,
        'imdbRating': mean_score,
        'releaseInfo': start_date,
        'description': synopsis
    }
