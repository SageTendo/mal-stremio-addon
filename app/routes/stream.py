from flask import Blueprint, abort

from .manifest import MANIFEST
from .utils import respond_with

stream_bp = Blueprint('stream', __name__)


@stream_bp.route('/<token>/stream/<stream_type>/<content_id>.json')
def addon_stream(token: str, stream_type: str, content_id: str):
    """
    Provides a stream for a specific content
    :param token: The user's API token for MyAnimeList
    :param stream_type: The type of stream of the content
    :param content_id: The ID of the content
    :return: JSON response
    """
    streams = []
    if stream_type not in MANIFEST['types']:
        abort(404)

    return respond_with({'stream': streams})
