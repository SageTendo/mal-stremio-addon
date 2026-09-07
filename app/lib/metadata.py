import random
import urllib.parse

import config


def get_transport_url(manifest_uri: str):
    base_url = f"{config.Config.PROTOCOL}://{config.Config.REDIRECT_URL}"
    url = f"{base_url}{manifest_uri}"
    return urllib.parse.quote_plus(url)


def to_stremio_genres(genres: list[str], transport_url, catalog_type, catalog_id):
    """Handle the genres from MAL and create Stremio genre links for them"""
    if not genres:
        return [], []

    links = []
    if transport_url:
        links = [
            {
                "name": genre,
                "category": "Genres",
                "url": f"stremio:///discover/{transport_url}/{catalog_type}/{catalog_id}"
                f"?genre={genre}",
            }
            for genre in genres
        ]
    return genres, links


def parse_background(background_objects: list[str]):
    """
    Handle the background object from MAL
    """
    if not background_objects:
        return None

    index = (
        random.randint(0, len(background_objects) - 1)
        if len(background_objects) > 1
        else 0
    )
    return background_objects[index]
