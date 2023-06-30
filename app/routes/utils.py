import random

from flask import jsonify

from app.routes import MAL_ID_PREFIX


# Enable CORS
def respond_with(data):
    """
    Respond with CORS headers
    :param data:
    :return:
    """
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = "*"
    resp.headers['Access-Control-Allow-Headers'] = '*'
    return resp


def mal_to_meta(anime_item: dict):
    """
    Convert MAL anime item to a valid Stremio meta format
    :param anime_item: The MAL anime item to convert
    :return: Stremio meta format
    """
    # Metadata stuff
    content_id = f"{MAL_ID_PREFIX}{anime_item.get('id')}"  # Format id to mal addon format

    title = anime_item.get('title')
    mean_score = anime_item.get('mean')
    synopsis = anime_item.get('synopsis')

    poster = None
    poster_objects = anime_item.get('main_picture')
    if poster_objects:
        poster = poster_objects.get('medium')
        # poster = poster_objects.get('large')

    genres = anime_item.get('genres')
    if genres:
        genres = [genre['name'] for genre in genres]

    start_date = anime_item.get('start_date')
    if start_date:
        start_date = start_date[:4]  # Get the year only or None

        # Format start date if end_date of airing was not returned
        end_date = anime_item.get('end_date')
        if not end_date:
            start_date += '-'

    # Check for background key in anime_item
    background = None
    picture_objects = anime_item.get('pictures')
    if picture_objects:
        # Get the first picture from the list of picture objects
        # index = 0

        # Get a random a picture from the list of picture objects
        index = random.randint(0, len(picture_objects) - 1)

        # Get the randomly chosen picture object's largest size
        background = picture_objects[index]['large']

    # Check for media type and filter out non series and movie types
    media_type = anime_item.get('media_type')
    if media_type:
        if media_type in ['ona', 'ova', 'special', 'tv', 'unknown']:
            media_type = 'series'
        elif media_type != 'movie':
            media_type = None

    return {
        'id': content_id,
        'name': title,
        'type': media_type,
        'genres': genres,
        'poster': poster,
        'background': background,
        'imdbRating': mean_score,
        'releaseInfo': start_date,
        'description': synopsis
    }
