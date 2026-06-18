from mal import (
    BadRequestError,
    ForbiddenError,
    HTTPError,
    NotFoundError,
    UnauthorizedError,
)
from quart import Blueprint, abort, url_for

import datetime
import config
from app.app import get_app
from app.lib.metadata import get_transport_url

from ..services.db import get_valid_user
from .manifest import MANIFEST
from .utils import log_error, respond_with

catalog_bp = Blueprint("catalog", __name__)


@catalog_bp.route(
    "/<user_id>/catalog/<string:catalog_type>/<string:catalog_id>.json",
    defaults={"extras": ""},
)
@catalog_bp.route(
    "/<user_id>/catalog/<string:catalog_type>/<string:catalog_id>/<path:extras>.json"
)
async def addon_catalog(
    user_id: str,
    catalog_type: str,
    catalog_id: str,
    extras: str,
):
    """
    Provides a list of anime from MyAnimeList
    :param user_id: The user's MyAnimeList ID
    :param catalog_type: The type of catalog to return
    :param catalog_id: The ID of the catalog to return, MAL divides a user's anime list into different categories
           (e.g. plan to watch, watching, completed, on hold, dropped)
    :param extras: A string of extra parameters to filter the results
    :return: JSON response
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
    nsfw_enabled = user.get("nsfw_enabled", False)
    transport_url = get_transport_url(
        url_for("manifest.addon_configured_manifest", user_id=user_id),
    )

    try:
        filters = _parse_stremio_filters(extras)
        offset = int(filters.get("skip", 0))
        genre = filters.get("genre", "")
        search = filters.get("search", "")

        if 0 < offset < 10:
            # Early return if offset less than 10
            # Stremio Web will spam the addon with requests for metas
            # to try and autofill with metas to fit the viewport
            return await respond_with({"metas": []}, stremio_response=True)

        if search:
            anime_list = await mal_service.search_anime(query=search, offset=offset)
        elif catalog_id == "seasonal":
            sort = user.get("sort_seasonal", config.DEFAULT_SEASONAL_SORT_OPTION)
            anime_list = await mal_service.get_seasonal_anime_list(
                token=token,
                year=datetime.datetime.now().year,
                season=filters.get("season", "summer"),
                offset=offset,
                sort=sort,
                nsfw=nsfw_enabled,
            )
        else:
            sort = user.get("sort_watchlist", config.DEFAULT_SORT_OPTION)
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
        return await respond_with({"metas": [], "message": str(e)}), 400
    except (BadRequestError, UnauthorizedError, ForbiddenError, NotFoundError) as e:
        return await respond_with({"metas": [], "message": e.message}), e.code or 400
    except HTTPError as e:
        log_error("HTTP_ERROR", str(e), e.message, e.code)
        return await respond_with({"metas": [], "message": str(e)}), 500


def _is_valid_catalog(catalog_type: str, catalog_id: str):
    if catalog_type not in MANIFEST["types"]:
        return False
    return any(catalog["id"] == catalog_id for catalog in MANIFEST["catalogs"])


def _parse_stremio_filters(extra: str | None) -> dict:
    """
    Converts:
        "genre=Action&search=batman&skip=20"
    into:
        {"genre": "Action", "search": "batman", "skip": "20"}
    """
    if not extra:
        return {}

    filters = {}
    for part in extra.split("&"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        filters[key] = value
    return filters
