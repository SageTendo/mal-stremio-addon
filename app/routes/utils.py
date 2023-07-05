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
    Convert MAL anime item to a Stremio's meta format
    :param anime_item: The MAL anime item to convert
    :return: Stremio's meta format
    """
    # Metadata stuff
    formatted_content_id = None
    if content_id := anime_item.get('id', None):
        # Format id to mal addon format
        formatted_content_id = f"{MAL_ID_PREFIX}{content_id}"

    # Get values of title, mean score, synopsis
    title = anime_item.get('title', None)
    mean_score = anime_item.get('mean', None)
    synopsis = anime_item.get('synopsis', None)

    # Check for poster key in anime_item
    poster = None
    if poster_objects := anime_item.get('main_picture', None):
        if poster := poster_objects.get('large', None):
            poster = poster_objects.get('medium')

    # Check for genres and format them if they exist
    if genres := anime_item.get('genres', None):
        genres = [genre['name'] for genre in genres]

    # Check for release info and format it if it exists
    if start_date := anime_item.get('start_date', None):
        start_date = start_date[:4]  # Get the year only
        start_date += '-'

        # Format start date if end_date of airing was not returned
        if end_date := anime_item.get('end_date', None):
            start_date += end_date

    # Check for background key in anime_item
    background = None
    if picture_objects := anime_item.get('pictures', None):
        # Get a random a picture from the list of picture objects
        index = random.randint(0, len(picture_objects) - 1)

        # Get the randomly chosen picture object's largest size if it exists else use medium
        if background := picture_objects[index].get('large', None) is None:
            background = picture_objects[index]['medium']

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
