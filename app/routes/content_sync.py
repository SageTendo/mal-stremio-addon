import urllib.parse
from typing import Optional

from quart import Blueprint
from requests import HTTPError

import config
from app.app import get_app
from app.lib.content_sync import UpdateStatus, handle_content_id
from app.routes.manifest import MANIFEST
from app.routes.utils import handle_api_error, respond_with
from app.services.db import get_valid_user

content_sync_bp = Blueprint("content_sync", __name__)


@content_sync_bp.route(
    "/<user_id>/subtitles/<string:content_type>/<string:content_id>/<string:_video_hash>.json"
)
@content_sync_bp.route(
    "/<user_id>/subtitles/<string:content_type>/<string:content_id>.json"
)
async def addon_content_sync(
    user_id: str, content_type: str, content_id: str, _video_hash: str = ""
):
    """
    Synchronize watched status for a specific content with MyAnimeList.
    Stremio will call this endpoint when a user watches a video, requesting a subtitle for it.
    The addon will assume the user has watched the content and will update the watched status in MyAnimeList.
    :param user_id: The user's API token for MyAnimeList
    :param content_type: The type of content
    :param content_id: The ID of the content
    :param _video_hash: The hash of the video (ignored)
    :return: JSON response

    TODO: Handle service errors
    """
    mal_service = get_app().mal

    content_id = urllib.parse.unquote(content_id)
    if content_type not in MANIFEST["types"]:
        return await respond_with(
            _create_sync_response(status=UpdateStatus.SKIP),
            cache_max_age=config.CONTENT_SYNC_ON_INVALID_DURATION,
            stale_revalidate=config.CONTENT_SYNC_ON_INVALID_DURATION,
            stale_error=config.CONTENT_SYNC_ON_INVALID_DURATION,
            stremio_response=True,
        )

    mal_id, current_episode = handle_content_id(content_id)
    if mal_id is None:
        return await respond_with(
            _create_sync_response(status=UpdateStatus.INVALID_ID),
            cache_max_age=config.CONTENT_SYNC_ON_INVALID_DURATION,
            stale_revalidate=config.CONTENT_SYNC_ON_INVALID_DURATION,
            stale_error=config.CONTENT_SYNC_ON_INVALID_DURATION,
            stremio_response=True,
        )

    user, error = get_valid_user(user_id)
    if error:
        return await respond_with(
            _create_sync_response(status=UpdateStatus.FAIL, message=error),
        )

    try:
        token = user.get("access_token", "")
        track_unlisted_anime = user.get("track_unlisted_anime", False)
        update_status = await mal_service.sync_anime_status(
            token=token,
            anime_id=mal_id,
            episode=current_episode,
            sync_unlisted=track_unlisted_anime,
        )
        return await respond_with(_create_sync_response(status=update_status))
    except HTTPError as err:
        handle_api_error(err)
        return await respond_with(
            _create_sync_response(status=UpdateStatus.FAIL),
        )


def _create_sync_response(status: UpdateStatus, message: Optional[str] = None):
    if not message:
        message = f"{status.name} - {status.value}"

    return {
        "subtitles": [{"id": 1, "url": "about:blank", "lang": status.value}],
        "message": f"{message}",
    }
