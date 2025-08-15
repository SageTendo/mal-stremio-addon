import functools
import urllib.parse

import requests
from flask import Blueprint

import config
from app.db.db import get_kitsu_id_from_mal_id
from app.routes import IMDB_ID_PREFIX, MAL_ID_PREFIX
from app.routes.auth import get_valid_user
from app.routes.manifest import MANIFEST
from app.routes.utils import handle_api_error, respond_with

stream_bp = Blueprint("stream", __name__)

limit = 15
providers = (
    "yts,eztv,rarbg,1337x,thepiratebay,kickasstorrents,"
    "torrentgalaxy,magnetdl,horriblesubs,nyaasi,tokyotosho,anidex"
)
quality_filters = "3Dbrremux,hdrall,dolbyvision,dolbyvisionwithhdr,threed"
TORRENTIO_API = f"https://torrentio.strem.fun/providers={providers}|qualityfilter={quality_filters}|limit={limit}"


@stream_bp.route("/<user_id>/stream/<content_type>/<content_id>.json")
def addon_stream(user_id: str, content_type: str, content_id: str):
    """
    Provide torrentio streams for movie content
    :param user_id: The id of the user requesting the content
    :param content_type: The type of content
    :param content_id: The id of the content
    :return: JSON response
    """
    # ignore imdb ids for older versions of mal-stremio
    if IMDB_ID_PREFIX in content_id:
        return respond_with({})

    content_id = urllib.parse.unquote(content_id)
    if content_type not in MANIFEST["types"]:
        return respond_with(
            {"streams": [], "message": "Content not supported"},
            cache_max_age=config.STREAM_ON_INVALID_DURATION,
            stale_revalidate=config.STREAM_ON_INVALID_DURATION,
            stale_error=config.STREAM_ON_INVALID_DURATION,
            stremio_response=True,
        )

    user, error = get_valid_user(user_id)
    if error:
        return respond_with({"streams": [], "message": error})

    if not user.get("fetch_streams", False):
        return respond_with(
            {"streams": [], "message": "Fetching streams is disabled"},
            cache_max_age=config.STREAM_ON_FAIL_TO_FETCH_DURATION,
            stale_revalidate=config.STREAM_ON_FAIL_TO_FETCH_DURATION,
            stale_error=config.STREAM_ON_FAIL_TO_FETCH_DURATION,
            stremio_response=True,
        )

    if content_id.startswith(MAL_ID_PREFIX):
        exists, kitsu_id = get_kitsu_id_from_mal_id(content_id)
    elif content_id.startswith("kitsu:"):
        exists, kitsu_id = True, content_id.replace("kitsu:", "")
    else:
        return respond_with(
            {"streams": [], "message": "Invalid content ID"},
            cache_max_age=config.STREAM_ON_INVALID_DURATION,
            stale_revalidate=config.STREAM_ON_INVALID_DURATION,
            stale_error=config.STREAM_ON_INVALID_DURATION,
            stremio_response=True,
        )

    if not exists:
        return respond_with(
            {"streams": [], "message": "No Kitsu ID in mapping database"},
            cache_max_age=config.STREAM_ON_NO_KITSU_ID_DURATION,
            stale_revalidate=config.STREAM_ON_NO_KITSU_ID_DURATION,
            stale_error=config.STREAM_ON_NO_KITSU_ID_DURATION,
            stremio_response=True,
        )

    try:
        url = f"{TORRENTIO_API}/stream/{content_type}/kitsu:{kitsu_id}.json"
        resp = fetch_streams(url)
        resp.raise_for_status()
        return respond_with(resp.json())
    except requests.HTTPError as e:
        handle_api_error(e)
        return respond_with({"streams": [], "message": "Failed to fetch streams"})


@functools.lru_cache(maxsize=config.STREAM_CACHE_SIZE)
def fetch_streams(url):
    return requests.get(url, headers=config.REQ_HEADERS, timeout=10)
