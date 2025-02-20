import functools
import urllib.parse

import httpx
from flask import Blueprint

from app.db.db import get_kitsu_id_from_mal_id
from app.routes import MAL_ID_PREFIX, IMDB_ID_PREFIX
from app.routes.manifest import MANIFEST
from app.routes.utils import respond_with

stream_bp = Blueprint('stream', __name__)

limit = 5
providers = ("yts,eztv,rarbg,1337x,thepiratebay,kickasstorrents,"
             "torrentgalaxy,magnetdl,horriblesubs,nyaasi,tokyotosho,anidex")
quality_filters = "brremux,hdrall,dolbyvision"
torrentio_api = f"https://torrentio.strem.fun/providers={providers}|qualityfilter={quality_filters}|limit={limit}"


@stream_bp.route('/<user_id>/stream/<content_type>/<content_id>.json')
async def addon_stream(user_id: str, content_type: str, content_id: str):
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
        return respond_with({'streams': [], 'message': 'Content not supported'}, ttl=60)

    if content_id.startswith(MAL_ID_PREFIX):
        exists, kitsu_id = get_kitsu_id_from_mal_id(content_id)
    elif content_id.startswith('kitsu:'):
        exists, kitsu_id = True, content_id.replace('kitsu:', '')
    else:
        return respond_with({'streams': [], 'message': 'Invalid content ID'}, ttl=60)

    if not exists:
        return respond_with({'streams': [], 'message': 'No Kitsu ID in mapping database'}, ttl=60)

    url = f"{torrentio_api}/stream/{content_type}/kitsu:{kitsu_id}.json"
    resp = await fetch_streams(url)
    if resp.is_error:
        return respond_with({'streams': [], 'message': 'No streams found'}, ttl=60)
    return respond_with(resp.json(), ttl=360)


@functools.lru_cache(maxsize=1000)
async def fetch_streams(url):
    async with httpx.AsyncClient() as client:
        return await client.get(url)
