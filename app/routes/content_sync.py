import urllib.parse
from datetime import datetime
from typing import Optional

from flask import Blueprint
from requests import HTTPError

import config
from app.db.db import get_mal_id_from_kitsu_id
from app.routes import MAL_ID_PREFIX, mal_client
from app.routes.auth import get_valid_user
from app.routes.manifest import MANIFEST
from app.routes.utils import handle_api_error, respond_with

content_sync_bp = Blueprint("content_sync", __name__)


class UpdateStatus:
    """Enumeration for anime update status"""

    OK = "MAL=OK"
    NULL = "MAL=NO_UPDATE"
    SKIP = "MAL=SKIPPED"
    INVALID_ID = "MAL=INVALID_ID"
    NOT_LIST = "MAL=NOT_LISTED"
    FAIL = "MAL=FAIL"


@content_sync_bp.route(
    "/<user_id>/subtitles/<content_type>/<content_id>/<video_hash>.json"
)
@content_sync_bp.route("/<user_id>/subtitles/<content_type>/<content_id>.json")
def addon_content_sync(
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
    """
    invalid_data = {
        "subtitles": [{"id": 1, "url": "about:blank", "lang": UpdateStatus.SKIP}],
        "message": None,
        "cacheMaxAge": config.CONTENT_SYNC_CACHE_ON_INVALID_DURATION,
        "staleRevalidate": config.CONTENT_SYNC_CACHE_ON_INVALID_DURATION,
        "staleError": config.CONTENT_SYNC_CACHE_ON_INVALID_DURATION,
    }

    content_id = urllib.parse.unquote(content_id)
    if content_type not in MANIFEST["types"]:
        invalid_data["message"] = "Content not supported"
        return respond_with(
            invalid_data,
            cache_max_age=invalid_data["cacheMaxAge"],
            stale_revalidate=invalid_data["staleRevalidate"],
            stale_error=invalid_data["staleError"],
        )

    mal_id, current_episode = handle_content_id(content_id)
    if mal_id is None:
        invalid_data["subtitles"][0]["lang"] = UpdateStatus.INVALID_ID
        invalid_data["message"] = "Invalid content ID"
        return respond_with(
            invalid_data,
            cache_max_age=invalid_data["cacheMaxAge"],
            stale_revalidate=invalid_data["staleRevalidate"],
            stale_error=invalid_data["staleError"],
        )

    try:
        user = get_valid_user(user_id)
        token = user.get("access_token")
        track_unlisted_anime = user.get("track_unlisted_anime", False)
        total_episodes, anime_listing_status = _get_anime_status(token, mal_id)

        if track_unlisted_anime and not anime_listing_status:
            # Fake a listing status if unlisted and user wants it tracked
            anime_listing_status = {"status": "watching", "num_episodes_watched": 0}
        elif not anime_listing_status:
            return respond_with(
                {
                    "subtitles": [
                        {"id": 1, "url": "about:blank", "lang": UpdateStatus.NOT_LIST}
                    ],
                    "message": "Content not in a watchlist",
                }
            )

        current_watch_status = anime_listing_status.get("status")
        num_episodes_watched = anime_listing_status.get("num_episodes_watched", 0)
        new_watch_status = handle_current_status(
            current_watch_status, current_episode, num_episodes_watched, total_episodes
        )
        if not new_watch_status:
            data = {
                "subtitles": [
                    {"id": 1, "url": "about:blank", "lang": UpdateStatus.NULL}
                ],
                "message": "No update required",
                "cacheMaxAge": config.CONTENT_SYNC_NO_UPDATE_DURATION,
                "staleRevalidate": config.DEFAULT_STALE_WHILE_REVALIDATE,
                "staleError": config.CONTENT_SYNC_NO_UPDATE_DURATION,
            }
            return respond_with(
                data,
                cache_max_age=data["cacheMaxAge"],
                stale_revalidate=data["staleRevalidate"],
                stale_error=data["staleError"],
            )

        start_date, finish_date = determine_watch_dates(
            anime_listing_status, current_episode, total_episodes
        )
        mal_client.update_watched_status(
            token,
            mal_id,
            current_episode,
            new_watch_status,
            start_date=start_date,
            finish_date=finish_date,
        )
        return respond_with(
            {
                "subtitles": [{"id": 1, "url": "about:blank", "lang": UpdateStatus.OK}],
                "message": "Content updated",
            }
        )
    except HTTPError as err:
        handle_api_error(err)
        return respond_with(
            {
                "subtitles": [
                    {"id": 1, "url": "about:blank", "lang": UpdateStatus.FAIL}
                ],
                "message": "Failed to update content",
            }
        )


def determine_watch_dates(
    anime_listing_status: dict, current_episode: int, total_episodes: int
):
    """
    Determine the dates to set for the start and finish dates of anime being watched, only if they have not been
    set before.The start date is set to the current date if the user is watching the first episode. The finish date
    is set to the current date if the user is watching the last episode.
    :param anime_listing_status: The listing status of the anime in the user's watchlist (if it exists or has been
    faked for unlisted anime tracking)
    :param current_episode: The current episode being watched
    :param total_episodes: The total number of episodes in the anime
    :return: A tuple of (start_date, finish_date)
    """
    start_date = anime_listing_status.get("start_date")
    finish_date = anime_listing_status.get("finish_date")
    num_episodes_watched = anime_listing_status.get("num_episodes_watched", 0)

    set_start = not start_date and current_episode == 1 and num_episodes_watched == 0
    set_finish = not finish_date and current_episode == total_episodes

    return (
        datetime.now().strftime("%Y-%m-%d") if set_start else start_date,
        datetime.now().strftime("%Y-%m-%d") if set_finish else finish_date,
    )


def handle_content_id(content_id: str):
    """
    Extract the ID of the content and the current episode.
    If ID is a Kitsu ID, get the relevant MAL ID from the database.
    :param content_id: The content ID
    :return: The ID of the content and the current episode
    """
    if content_id.startswith(MAL_ID_PREFIX):
        return content_id.replace(f"{MAL_ID_PREFIX}_", ""), 1  # Assume episode

    if content_id.startswith("kitsu:"):
        content_id = content_id.replace("kitsu:", "")
        current_episode = 1

        if content_id.count(":") == 1:  # Handle series
            content_id, current_episode = content_id.split(":")

        exists, mal_id = get_mal_id_from_kitsu_id(content_id)
        if exists:
            return mal_id, int(current_episode)
    return None, -1


def _get_anime_status(token: str, mal_id: str):
    fields = "num_episodes my_list_status"
    resp = mal_client.get_anime_details(token, mal_id, fields=fields)
    total_episodes = resp.get("num_episodes", 0)
    list_status = resp.get("my_list_status", None)
    return total_episodes, list_status


def handle_current_status(
    status: str, current_episode: int, watched_episodes: int, total_episodes: int
) -> Optional[str]:
    if status in {"watching", "plan_to_watch", "on_hold"}:
        if current_episode == total_episodes:
            return "completed"
        if current_episode > watched_episodes:
            return "watching"
    return None
