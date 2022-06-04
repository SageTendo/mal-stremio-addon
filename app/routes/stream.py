from flask import Blueprint, abort

from .manifest import MANIFEST
from .utils import respond_with

stream_bp = Blueprint('stream', __name__)


@stream_bp.route('/<token>/stream/<stream_type>/<content_id>.json')
def addon_stream(token: str, stream_type: str, content_id: str):
    streams = []
    if stream_type not in MANIFEST['types']:
        abort(404)

    return respond_with({'stream': streams})
