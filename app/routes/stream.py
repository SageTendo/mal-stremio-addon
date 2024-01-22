from flask import Blueprint, abort

from .manifest import MANIFEST
from .utils import respond_with

stream_bp = Blueprint('stream', __name__)

torrentio_API = "https://torrentio.strem.fun/stream/"
torrentio_lite_API = "https://torrentio.strem.fun/lite/stream/"


@stream_bp.route('/<user_id>/stream/<stream_type>/<content_id>.json')
def addon_stream(user_id: str, stream_type: str, content_id: str):
    """
    Provides a stream for a specific content
    :param user_id: The user's MyAnimeList ID
    :param stream_type: The type of stream of the content
    :param content_id: The ID of the content
    :return: JSON response
    """
    streams = []
    if stream_type not in MANIFEST['types']:
        abort(404)

    return respond_with({'stream': streams})
