import ast
import random
import re
import urllib.parse
from typing import Optional

import requests
from flask import Blueprint, Request, abort, request, url_for

import config

from . import MAL_ID_PREFIX, mal_client
from .auth import get_valid_user
from .manifest import MANIFEST
from .utils import handle_api_error, respond_with

catalog_bp = Blueprint("catalog", __name__)


@catalog_bp.route("/<user_id>/catalog/<catalog_type>/<catalog_id>.json")
@catalog_bp.route("/<user_id>/catalog/<catalog_type>/<catalog_id>/search=<search>.json")
@catalog_bp.route("/<user_id>/catalog/<catalog_type>/<catalog_id>/skip=<offset>.json")
@catalog_bp.route("/<user_id>/catalog/<catalog_type>/<catalog_id>/genre=<genre>.json")
@catalog_bp.route(
    "/<user_id>/catalog/<catalog_type>/<catalog_id>/genre=<genre>&search=<search>.json"
)
@catalog_bp.route(
    "/<user_id>/catalog/<catalog_type>/<catalog_id>/skip=<offset>&search=<search>.json"
)
@catalog_bp.route(
    "/<user_id>/catalog/<catalog_type>/<catalog_id>/skip=<offset>.json&genre=<genre>&search=<search>.json"
)
def addon_catalog(
    user_id: str,
    catalog_type: str,
    catalog_id: str,
    offset: str = "",
    genre: str = "",
    search: str = "",
):
    """
    Provides a list of anime from MyAnimeList
    :param user_id: The user's MyAnimeList ID
    :param catalog_type: The type of catalog to return
    :param catalog_id: The ID of the catalog to return, MAL divides a user's anime list into different categories
           (e.g. plan to watch, watching, completed, on hold, dropped)
    :param offset: The number of items to skip
    :param genre: The genre to filter by
    :param search: Used to search globally for an anime on MyAnimeList
    :return: JSON response
    """
    if not _is_valid_catalog(catalog_type, catalog_id):
        abort(404)

    user = get_valid_user(user_id)
    token = user.get("access_token")
    sort = user.get("sort_watchlist", config.DEFAULT_SORT_OPTION)

    try:
        response_data = _fetch_anime_list(token, search, catalog_id, offset, sort=sort)
        anime_list = [x["node"] for x in response_data.get("data", [])]
        filtered_anime_list = filter(lambda x: _has_genre_tag(x, genre), anime_list)
        meta_previews = [
            _mal_to_meta(
                anime_item,
                catalog_type=catalog_type,
                catalog_id=catalog_id,
                transport_url=_get_transport_url(request, user_id),
            )
            for anime_item in filtered_anime_list
        ]

        return respond_with(
            {"metas": meta_previews},
            private=True,
            cache_max_age=config.CATALOG_ON_SUCCESS_DURATION,
            stale_revalidate=config.CATALOG_STALE_WHILE_REVALIDATE,
            stale_error=config.CATALOG_STALE_IF_ERROR,
            stremio_response=True,
        )
    except ValueError as e:
        return respond_with({"metas": [], "message": str(e)}), 400
    except requests.HTTPError as e:
        handle_api_error(e)
        return respond_with({"metas": []}), e.response.status_code


def _get_transport_url(req: Request, user_id: str, parameters: str = ""):
    url = req.url[:-1] + url_for(
        "manifest.addon_configured_manifest", user_id=user_id, parameters=parameters
    )
    return urllib.parse.quote_plus(url)


def _is_valid_catalog(catalog_type: str, catalog_id: str):
    if catalog_type not in MANIFEST["types"]:
        return False
    return any(catalog["id"] == catalog_id for catalog in MANIFEST["catalogs"])


def _has_genre_tag(meta: dict, genre: str = ""):
    if not genre:
        return True

    # Handle stremio link object
    decoded_string = urllib.parse.unquote(genre)
    if re.search(r"\{.*}", decoded_string):
        formatted_genre = ast.literal_eval(decoded_string)["name"]
    else:
        formatted_genre = genre

    return any(
        formatted_genre.lower() == genre["name"].lower()
        for genre in meta.get("genres", [])
    )


def _fetch_anime_list(token, search, catalog_id, offset, **kwargs):
    if search and len(search) < 3:
        raise ValueError("Search query must be at least 3 characters long")

    return_fields = "media_type genres mean start_date end_date synopsis"
    if search:
        return mal_client.get_anime_list(
            token, query=search, offset=offset, fields=return_fields
        )

    return mal_client.get_user_anime_list(
        token, status=catalog_id, offset=offset, fields=return_fields, **kwargs
    )


def _mal_to_meta(
    anime_item: dict, catalog_type: str, catalog_id: str, transport_url: str
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
        formatted_content_id = f"{MAL_ID_PREFIX}_{content_id}"

    title = anime_item.get("title")
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
        "background": background,
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
    links = [
        {
            "name": genre["name"],
            "category": "Genres",
            "url": f"stremio:///discover/{transport_url}/{catalog_type}/{catalog_id}"
            f"?genre={genre}",
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
    return random_image.get("large") or random_image.get("medium")
