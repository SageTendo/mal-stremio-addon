import logging
import urllib.parse

import httpx
import requests
from flask import Blueprint, abort

from app.routes import IMDB_ID_PREFIX, MAL_ID_PREFIX
from app.routes.content_sync import haglund_API
from app.routes.utils import respond_with

stream_bp = Blueprint('stream', __name__)

limit = 5
providers = ("yts,eztv,rarbg,1337x,thepiratebay,kickasstorrents,"
             "torrentgalaxy,magnetdl,horriblesubs,nyaasi,tokyotosho,anidex")
quality_filters = "brremux,hdrall,dolbyvision"
torrentio_api = f"https://torrentio.strem.fun/providers={providers}|qualityfilter={quality_filters}|limit={limit}"


@stream_bp.route('/<user_id>/stream/<content_type>/<content_id>.json')
async def addon_stream(user_id: str, content_type: str, content_id: str):
    if IMDB_ID_PREFIX in content_id:
        return respond_with({})

    if content_type != 'movie':
        return respond_with({})

    # Fetch kitsu id from mapper
    content_id = urllib.parse.unquote(content_id)
    content_id = content_id.replace(f"{MAL_ID_PREFIX}_", '')
    content_id = int(content_id)

    async with httpx.AsyncClient() as client:
        resp = await client.get(haglund_API, params={'source': 'myanimelist', 'id': content_id})

        if resp.status_code >= 400:
            logging.error(resp.status_code, resp.reason_phrase)
            abort(404)

        # Extract the kitsu id and fetch torrentio streams
        kitsu_id = resp.json().get('kitsu', None)
        if kitsu_id is None:
            logging.warning("Stream => No id for Kitsu found")
            abort(404)

        kitsu_id = f"kitsu:{kitsu_id}"

        resp = await client.get(f"{torrentio_api}/stream/{content_type}/{kitsu_id}.json")
        return respond_with(resp.json())
