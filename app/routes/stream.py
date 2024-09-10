import urllib.parse

import httpx
from flask import Blueprint

from app.db.db import get_kitsu_id_from_mal_id
from app.routes import MAL_ID_PREFIX
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
    content_id = urllib.parse.unquote(content_id)
    if (MAL_ID_PREFIX not in content_id) or (content_type != 'movie'):
        return respond_with({})

    async with httpx.AsyncClient() as client:
        kitsu_id = get_kitsu_id_from_mal_id(content_id)
        resp = await client.get(f"{torrentio_api}/stream/{content_type}/kitsu:{kitsu_id}.json")
        return respond_with(resp.json())
