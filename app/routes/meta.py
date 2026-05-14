import kitsu
from mal import (
    BadRequestError,
    ForbiddenError,
    HTTPError,
    NotFoundError,
    UnauthorizedError,
)
from quart import Blueprint, abort, url_for

import config
from app.app import get_app
from app.lib.metadata import get_transport_url

from ..services.db import get_kitsu_id_from_mal_id, get_valid_user
from .manifest import MANIFEST
from .utils import log_error, respond_with

meta_bp = Blueprint("meta", __name__)


@meta_bp.route("/<user_id>/meta/<string:meta_type>/<string:meta_id>.json")
async def addon_meta(user_id: str, meta_type: str, meta_id: str):
    """
    Provides metadata for a specific content
    :param user_id: The user's MyAnimeList ID
    :param meta_type: The type of metadata to return
    :param meta_id: The ID of the content
    :return: JSON response
    """
    mal_service = get_app().mal
    kitsu_service = get_app().kitsu

    # ignore imdb ids for older versions of mal-stremio
    if config.IMDB_ID_PREFIX in meta_id:
        return await respond_with(
            {"meta": {}},
            cache_max_age=config.META_ON_INVALID_DURATION,
            stale_revalidate=config.META_ON_INVALID_DURATION,
            stale_error=config.META_ON_INVALID_DURATION,
            stremio_response=True,
        )

    if meta_type not in MANIFEST["types"]:
        abort(404)

    user, error = get_valid_user(user_id)
    if error:
        return await respond_with({"meta": {}, "message": error})

    try:
        kitsu_anime = None
        if meta_id.startswith(config.KITSU_ID_PREFIX):
            kitsu_anime = await kitsu_service.get_anime_by_id(meta_id)
        elif meta_id.startswith(config.MAL_ID_PREFIX):
            exists, kitsu_id = get_kitsu_id_from_mal_id(meta_id)
            if exists:
                kitsu_anime = await kitsu_service.get_anime_by_id(kitsu_id)
            else:
                token = user.get("access_token", "")
                anime = await mal_service.get_anime_details(anime_id=meta_id, token=token)
                kitsu_anime = await kitsu_service.get_anime_by_title(
                    anime.title.english or anime.title.japanese or ""
                )

        if not kitsu_anime:
            return (
                await respond_with({"meta": {}, "message": "No Kitsu anime found"}),
                404,
            )

        user_id = user.get("uid", "")
        transport_url = get_transport_url(
            url_for("manifest.addon_configured_manifest", user_id=user_id)
        )

        meta = await kitsu_service.to_stremio_meta(
            mal_id=meta_id,
            anime=kitsu_anime,
            transport_url=transport_url,
        )

        return await respond_with(
            {"meta": meta},
            cache_max_age=config.META_ON_SUCCESS_DURATION,
            stale_revalidate=config.DEFAULT_STALE_WHILE_REVALIDATE,
            stale_error=config.META_ON_SUCCESS_DURATION,
            stremio_response=True,
        )
    except (BadRequestError, UnauthorizedError, ForbiddenError, NotFoundError) as e:
        return await respond_with({"meta": {}, "message": str(e)}), e.code
    except (
        kitsu.errors.BadRequest,
        kitsu.errors.Unauthorized,
        kitsu.errors.Forbidden,
    ) as e:
        code = e.response_code or 400
        return (await respond_with({"meta": {}, "message": e.message}), code)
    except HTTPError as e:
        log_error("MAL_ERROR", str(e), e.message, e.code)
        return await respond_with({"meta": {}, "message": str(e)}), 500
    except kitsu.errors.HTTPException as e:
        code = e.response_code or 500
        log_error("KITSU_ERROR", str(e), e.message, code)
        return (await respond_with({"meta": {}, "message": str(e)}), 500)
