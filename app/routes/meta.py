import logging
from functools import lru_cache

import requests
from flask import Blueprint, abort

from . import IMDB_ID_PREFIX, MAL_ID_PREFIX
from .manifest import MANIFEST
from .utils import respond_with
from ..db.db import get_kitsu_id_from_mal_id

meta_bp = Blueprint('meta', __name__)

kitsu_API = "https://anime-kitsu.strem.fun/meta"
HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0",
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}


@meta_bp.route('/<user_id>/meta/<meta_type>/<meta_id>.json')
@lru_cache(maxsize=1000)
def addon_meta(user_id: str, meta_type: str, meta_id: str):
    """
    Provides metadata for a specific content
    :param user_id: The user's API token for MyAnimeList
    :param meta_type: The type of metadata to return
    :param meta_id: The ID of the content
    :return: JSON response
    """
    # ignore imdb ids for older versions of mal-stremio
    if IMDB_ID_PREFIX in meta_id:
        return respond_with({})

    if meta_type not in MANIFEST['types']:
        abort(404)

    exists, kitsu_id = get_kitsu_id_from_mal_id(meta_id)
    if exists:
        resp = requests.get(headers=HEADERS,
                            url=f"{kitsu_API}/{meta_type}/kitsu:{kitsu_id}.json")
    else:  # if no kitsu id, try with mal id
        mal_id = meta_id.replace(f"{MAL_ID_PREFIX}_", '')
        resp = requests.get(headers=HEADERS,
                            url=f"{kitsu_API}/{meta_type}/mal:{mal_id}.json")

    if not resp.ok:
        logging.error(resp.status_code, resp.reason)
        abort(404, f"{resp.status_code}: {resp.reason}")

    meta = kitsu_to_meta(resp.json())
    meta['id'] = meta_id
    meta['type'] = meta_type
    return respond_with({'meta': meta})


def kitsu_to_meta(kitsu_meta: dict) -> dict:
    """
    Convert kitsu item to a valid Stremio meta format
    :param kitsu_meta: The kitsu item to convert
    :return: Stremio meta format
    """
    meta = kitsu_meta.get('meta', {})

    kitsu_id = meta.get('id', '').replace('kitsu:', '')
    name = meta.get('name', '')
    genres = meta.get('genres', [])
    logo = meta.get('logo', None)
    poster = meta.get('poster', None)
    background = meta.get('background', None)
    description = meta.get('description', None)
    releaseInfo = meta.get('releaseInfo', None)
    year = meta.get('year', None)
    imdbRating = meta.get('imdbRating', None)
    trailers = meta.get('trailers', [])
    links = meta.get('links', [])
    cacheMaxAge = meta.get('cacheMaxAge', None)
    runtime = meta.get('runtime', None)
    videos = meta.get('videos', [])
    imdb_id = meta.get('imdb_id', None)

    return {
        'cacheMaxAge': cacheMaxAge,
        'staleRevalidate': 43200,
        'staleError': 3600,

        'kitsu_id': kitsu_id,
        'name': name,
        'genres': genres,
        'logo': logo,
        'poster': poster,
        'background': background,
        'description': description,
        'releaseInfo': releaseInfo,
        'year': year,
        'imdbRating': imdbRating,
        'trailers': trailers,
        'links': links,
        'runtime': runtime,
        'videos': videos,
        'imdb_id': imdb_id
    }
