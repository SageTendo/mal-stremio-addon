import functools
import urllib.parse

import httpx
from flask import Blueprint

import config
from app.db.db import get_kitsu_id_from_mal_id
from app.routes import MAL_ID_PREFIX, IMDB_ID_PREFIX
from app.routes.auth import get_token
from app.routes.manifest import MANIFEST
from app.routes.utils import respond_with

stream_bp = Blueprint('stream', __name__)

limit = 15
providers = ("yts,eztv,rarbg,1337x,thepiratebay,kickasstorrents,"
             "torrentgalaxy,magnetdl,horriblesubs,nyaasi,tokyotosho,anidex")
quality_filters = "3Dbrremux,hdrall,dolbyvision,dolbyvisionwithhdr,threed"
torrentio_api = f"https://torrentio.strem.fun/providers={providers}|qualityfilter={quality_filters}|limit={limit}"


@stream_bp.route('/<user_id>/stream/<content_type>/<content_id>.json')
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
    if content_type not in MANIFEST['types']:
        return respond_with({'streams': [], 'message': 'Content not supported'}, ttl=config.STREAM_CACHE_EXPIRE)

    get_token(user_id)
    if content_id.startswith(MAL_ID_PREFIX):
        exists, kitsu_id = get_kitsu_id_from_mal_id(content_id)
    elif content_id.startswith('kitsu:'):
        exists, kitsu_id = True, content_id.replace('kitsu:', '')
    else:
        return respond_with({'streams': [], 'message': 'Invalid content ID'}, ttl=360)

    if not exists:
        return respond_with({'streams': [], 'message': 'No Kitsu ID in mapping database'}, ttl=360)

    url = f"{torrentio_api}/stream/{content_type}/kitsu:{kitsu_id}.json"
    resp = fetch_streams(url)
    if resp.is_error:
        return respond_with({'streams': [], 'message': 'No streams found'}, ttl=180)
    return respond_with(resp.json(), ttl=config.STREAM_CACHE_EXPIRE, immutable=True)


@functools.lru_cache(maxsize=config.STREAM_CACHE_SIZE)
def fetch_streams(url):
    with httpx.Client() as client:
        return client.get(url)
