import random
import urllib.parse
from typing import Optional

import config
from app.routes import MAL_ID_PREFIX


def get_transport_url(manifest_uri: str):
    base_url = f"{config.Config.PROTOCOL}://{config.Config.REDIRECT_URL}"
    url = f"{base_url}{manifest_uri}"
    return urllib.parse.quote_plus(url)


def mal_to_meta(
    anime_item: dict,
    catalog_type: str = "anime",
    catalog_id: str = "plan_to_watch",
    transport_url: str = "",
):
    """
    Convert MAL anime item to a valid Stremio meta format
    :param anime_item: The MAL anime item to convert
    :param catalog_type: The type of catalog being referenced in the link meta object
    :param catalog_id: The id of catalog being referenced in the link meta object
    :param transport_url: The url to the addon's manifest.json
    :return: Stremio meta format
    """
    formatted_content_id = None
    if content_id := anime_item.get("id"):
        formatted_content_id = f"{MAL_ID_PREFIX}{content_id}"

    title = anime_item.get("alternative_titles", {}).get("en") or anime_item.get(
        "title"
    )
    synopsis = anime_item.get("synopsis")
    poster = _handle_poster_object(anime_item.get("main_picture", {}))

    anime_item_genres = anime_item.get("genres")
    genres, links = _handle_genres_with_links(
        anime_item_genres, transport_url, catalog_type, catalog_id
    )

    mean_score: Optional[str] = None
    if score := anime_item.get("mean"):
        mean_score = str(score)

    if start_date := anime_item.get("start_date"):
        start_date = start_date[:4]  # Get the year only
        start_date += "-"

        if end_date := anime_item.get("end_date"):
            start_date += end_date[:4]

    picture_objects = anime_item.get("pictures", [])
    background = _handle_background_object(picture_objects)

    if media_type := anime_item.get("media_type"):
        if media_type in ["ona", "ova", "special", "tv", "unknown"]:
            media_type = "series"
        elif media_type != "movie":
            media_type = None

    return {
        "id": formatted_content_id,
        "name": title,
        "type": media_type,
        "genres": genres,
        "links": links,
        "poster": poster,
        "background": background if background else poster,
        "imdbRating": mean_score,
        "releaseInfo": start_date,
        "description": synopsis,
    }


def _handle_poster_object(poster_object):
    """
    Handle the poster object from MAL
    """
    if not poster_object:
        return None
    return poster_object.get("large") or poster_object.get("medium")


def _handle_genres_with_links(genres, transport_url, catalog_type, catalog_id):
    """Handle the genres from MAL and create Stremio genre links for them"""
    if not genres:
        return [], []

    formatted_genres = [genre["name"] for genre in genres]
    links = []
    if transport_url:
        links = [
            {
                "name": genre["name"],
                "category": "Genres",
                "url": f"stremio:///discover/{transport_url}/{catalog_type}/{catalog_id}"
                f"?genre={genre['name']}",
            }
            for genre in genres
        ]
    return formatted_genres, links


def _handle_background_object(background_objects):
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
    random_image = background_objects[index]
    return random_image.get("medium") or random_image.get("large")
