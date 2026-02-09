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


def kitsu_to_meta(kitsu_meta: dict) -> dict:
    """
    Convert kitsu item to a valid Stremio meta format
    :param kitsu_meta: The kitsu item to convert
    :return: Stremio meta format
    """
    meta = kitsu_meta.get("meta", {})

    kitsu_id = meta.get("id", "").replace("kitsu:", "")
    name = meta.get("name", "")
    genres = meta.get("genres", [])
    logo = meta.get("logo", None)
    poster = meta.get("poster", None)
    background = meta.get("background", None)
    description = meta.get("description", None)
    release_info = meta.get("releaseInfo", None)
    year = meta.get("year", None)
    imdb_rating = meta.get("imdbRating", None)
    trailers = meta.get("trailers", [])
    links = meta.get("links", [])
    runtime = meta.get("runtime", None)
    videos = meta.get("videos", [])
    imdb_id = meta.get("imdb_id", None)

    return {
        "kitsu_id": kitsu_id,
        "name": name,
        "genres": genres,
        "logo": logo,
        "poster": poster,
        "background": background,
        "description": description,
        "releaseInfo": release_info,
        "year": year,
        "imdbRating": imdb_rating,
        "trailers": trailers,
        "links": links,
        "runtime": runtime,
        "videos": videos,
        "imdb_id": imdb_id,
    }
