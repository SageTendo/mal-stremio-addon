import ast
import re
import urllib.parse

import requests
from quart import Blueprint, abort, url_for

import config
from app.lib.metadata import get_transport_url, mal_to_meta

from . import mal_client
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
async def addon_catalog(
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

    user, error = get_valid_user(user_id)
    if error:
        metas = [
            {
                "id": f"mal:{i}",
                "type": "anime",
                "name": "Error",
                "description": error,
            }
            for i in range(30)  # 30 metas to keep the UI consistent
        ]
        return await respond_with({"metas": metas}, stremio_response=True)

    try:
        token = user.get("access_token")
        sort = user.get("sort_watchlist", config.DEFAULT_SORT_OPTION)
        nsfw_enabled = user.get("nsfw_enabled", False)
        response_data = _fetch_anime_list(
            token, search, catalog_id, offset, sort=sort, nsfw=nsfw_enabled
        )

        anime_list = [x["node"] for x in response_data.get("data", [])]
        filtered_anime_list = filter(lambda x: _has_genre_tag(x, genre), anime_list)
        meta_previews = [
            mal_to_meta(
                anime_item,
                catalog_type=catalog_type,
                catalog_id=catalog_id,
                transport_url=get_transport_url(
                    url_for("manifest.addon_configured_manifest", user_id=user_id),
                ),
            )
            for anime_item in filtered_anime_list
        ]

        return await respond_with(
            {"metas": meta_previews},
            private=True,
            cache_max_age=config.CATALOG_ON_SUCCESS_DURATION,
            stale_revalidate=config.CATALOG_STALE_WHILE_REVALIDATE,
            stale_error=config.CATALOG_STALE_IF_ERROR,
            stremio_response=True,
        )
    except ValueError as e:
        return await respond_with({"metas": [], "message": str(e)}), 400
    except requests.HTTPError as e:
        handle_api_error(e)
        return await respond_with({"metas": []}), e.response.status_code


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


def _fetch_anime_list(token, search, catalog_id, offset, nsfw=False, **kwargs):
    if search and len(search) < 3:
        raise ValueError("Search query must be at least 3 characters long")

    return_fields = (
        "alternative_titles,media_type,genres,mean,start_date,end_date,synopsis"
    )
    if search:
        return mal_client.get_anime_list(
            token,
            query=search,
            offset=offset,
            fields=return_fields,
            nsfw=nsfw,
            **kwargs,
        )

    return mal_client.get_user_anime_list(
        token,
        status=catalog_id,
        offset=offset,
        fields=return_fields,
        nsfw=nsfw,
        **kwargs,
    )
