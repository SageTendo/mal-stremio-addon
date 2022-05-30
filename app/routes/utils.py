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
    content_id = f"mal-{anime_item['id']}"
    poster_objects = anime_item['main_picture']
    poster = poster_objects['medium']
    # poster = poster_objects['large']
    genres = [genre['name'] for genre in anime_item['genres']]
    rating = anime_item['mean'] if 'mean' in anime_item.keys() else 0
    start_date = anime_item['start_date'][:4]  # Get the year only
    description = anime_item['synopsis']

    # Check for background key in anime_item
    background = ''
    if 'pictures' in anime_item.keys():
        # Get the first picture from the list of picture objects
        # index = 0

        # Get a random a picture from the list of picture objects
        index = random.randint(0, len(anime_item['pictures']) - 1)

        # Get the randomly chosen picture object's largest size
        background = anime_item['pictures'][index]['large']

    # Format start date if end_date of airing was returned
    if 'end_date' not in anime_item.keys():
        start_date += '-'

    return {
        'id': content_id,
        'type': content_type,
        'name': anime_item['title'],
        'genres': genres,
        'poster': poster,
        'background': background,
        'imdbRating': rating,
        'releaseInfo': start_date,
        'description': description
    }
