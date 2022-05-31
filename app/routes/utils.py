import random

from flask import jsonify


# Enable CORS
def respond_with(data):
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = "*"
    resp.headers['Access-Control-Allow-Headers'] = '*'
    return resp


def mal_to_meta(anime_item: dict, content_type: str):
    # Metadata stuff
    content_id = f"mal-{anime_item['id']}"  # Format id to mal addon format

    title = None
    if 'title' in anime_item.keys():
        title = anime_item['title']

    poster = None
    if 'main_picture' in anime_item.keys():
        poster_objects = anime_item['main_picture']
        poster = poster_objects['medium']
        # poster = poster_objects['large']

    genres = None
    if 'genres' in anime_item.keys():
        genres = [genre['name'] for genre in anime_item['genres']]

    mean_score = None
    if 'mean' in anime_item.keys():
        mean_score = anime_item['mean']

    synopsis = None
    if 'synopsis' in anime_item.keys():
        synopsis = anime_item['synopsis']

    start_date = None
    if 'start_date' in anime_item.keys():
        start_date = anime_item['start_date'][:4]  # Get the year only or None

        # Format start date if end_date of airing was not returned
        if 'end_date' not in anime_item.keys():
            start_date += '-'

    # Check for background key in anime_item
    background = None
    if 'pictures' in anime_item.keys():
        # Get the first picture from the list of picture objects
        # index = 0

        # Get a random a picture from the list of picture objects
        index = random.randint(0, len(anime_item['pictures']) - 1)

        # Get the randomly chosen picture object's largest size
        background = anime_item['pictures'][index]['large']

    return {
        'id': content_id,
        'name': title,
        'type': content_type,
        'genres': genres,
        'poster': poster,
        'background': background,
        'imdbRating': mean_score,
        'releaseInfo': start_date,
        'description': synopsis
    }
