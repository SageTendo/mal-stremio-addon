import requests
from quart import Blueprint, abort, url_for

import config
from app.app import get_app
from app.lib.metadata import get_transport_url

from ..services.db import get_valid_user
from .manifest import MANIFEST
from .utils import handle_api_error, log_error, respond_with

catalog_bp = Blueprint("catalog", __name__)


@catalog_bp.route("/<user_id>/catalog/<string:catalog_type>/<string:catalog_id>.json")
@catalog_bp.route(
    "/<user_id>/catalog/<string:catalog_type>/<string:catalog_id>/search=<string:search>.json"
)
@catalog_bp.route(
    "/<user_id>/catalog/<string:catalog_type>/<string:catalog_id>/skip=<int:offset>.json"
)
@catalog_bp.route(
    "/<user_id>/catalog/<string:catalog_type>/<string:catalog_id>/genre=<string:genre>.json"
)
@catalog_bp.route(
    "/<user_id>/catalog/<string:catalog_type>/<catalog_id>/genre=<string:genre>&search=<string:search>.json"
)
@catalog_bp.route(
    "/<user_id>/catalog/<string:catalog_type>/<catalog_id>/skip=<int:offset>&search=<string:search>.json"
)
@catalog_bp.route(
    "/<user_id>/catalog/<string:catalog_type>/<catalog_id>/skip=<int:offset>&genre=<string:genre>&search=<string:search>.json"
)
async def addon_catalog(
    user_id: str,
    catalog_type: str,
    catalog_id: str,
    offset: int = 0,
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

    TODO: Handle service errors
    """
    current_app = get_app()
    mal_service = current_app.mal

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

    token = user.get("access_token", "")
    sort = user.get("sort_watchlist", config.DEFAULT_SORT_OPTION)
    nsfw_enabled = user.get("nsfw_enabled", False)
    transport_url = get_transport_url(
        url_for("manifest.addon_configured_manifest", user_id=user_id),
    )

    try:
        if search:
            anime_list = await mal_service.search_anime(query=search, offset=offset)
        else:
            anime_list = await mal_service.get_user_anime_list(
                token=token,
                status=catalog_id,
                offset=offset,
                sort=sort,
                nsfw=nsfw_enabled,
            )

        filtered_anime_list = mal_service.filter_anime(anime_list, genre)
        return await respond_with(
            {
                "metas": [
                    mal_service.to_stremio_meta(
                        anime=anime,
                        catalog_type=catalog_type,
                        catalog_id=catalog_id,
                        transport_url=transport_url,
                    )
                    for anime in filtered_anime_list
                ]
            },
            private=True,
            cache_max_age=config.CATALOG_ON_SUCCESS_DURATION,
            stale_revalidate=config.CATALOG_STALE_WHILE_REVALIDATE,
            stale_error=config.CATALOG_STALE_IF_ERROR,
            stremio_response=True,
        )
    except ValueError as e:
        log_error("VALUE ERROR", str(e), __name__)
        return await respond_with({"metas": [], "message": str(e)}), 400
    except requests.HTTPError as e:
        handle_api_error(e)
        return await respond_with({"metas": []}), e.response.status_code


def _is_valid_catalog(catalog_type: str, catalog_id: str):
    if catalog_type not in MANIFEST["types"]:
        return False
    return any(catalog["id"] == catalog_id for catalog in MANIFEST["catalogs"])
