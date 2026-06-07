from datetime import date
from enum import Enum
from typing import Optional

from mal import WatchStatus

import config
from app.services.anime_mapping import get_mal_id_from_kitsu_id


class UpdateStatus(Enum):
    """Enumeration for anime update status"""

    OK = "MAL=OK"
    NULL = "MAL=NO_UPDATE"
    SKIP = "MAL=SKIPPED"
    INVALID_ID = "MAL=INVALID_ID"
    NOT_LIST = "MAL=NOT_LISTED"
    FAIL = "MAL=FAILED_UPDATE"


def handle_current_status(
    status: str, current_episode: int, watched_episodes: int, total_episodes: int
) -> Optional[str]:
    if status in {"watching", "plan_to_watch", "on_hold"}:
        if total_episodes > 0 and current_episode >= total_episodes:
            return "completed"
        if current_episode > watched_episodes:
            return "watching"
    return None


def _parse_id_and_episode(content_id: str) -> tuple[str, int]:
    current_episode = 1
    parts = content_id.split(":")

    if len(parts) >= 2:
        content_id, current_episode_str = parts[:2]
        if current_episode_str.isdigit():
            current_episode = int(current_episode_str)
    return content_id, current_episode


def handle_content_id(content_id: str) -> tuple[Optional[str], int]:
    """
    Extract the ID of the content and the current episode.
    If ID is a Kitsu ID, get the relevant MAL ID from the database.
    :param content_id: The content ID
    :return: The ID of the content and the current episode
    """
    if content_id.startswith(config.MAL_ID_PREFIX):
        return _parse_id_and_episode(content_id.replace(config.MAL_ID_PREFIX, ""))

    if content_id.startswith(config.KITSU_ID_PREFIX):
        kitsu_id, current_episode = _parse_id_and_episode(
            content_id.replace(config.KITSU_ID_PREFIX, "")
        )
        exists, mal_id = get_mal_id_from_kitsu_id(kitsu_id)
        if exists:
            return str(mal_id), current_episode
    return None, -1


def determine_watch_dates(
    watch_status: Optional[WatchStatus],
    current_episode: int,
    total_episodes: int,
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
    today = date.today().strftime("%Y-%m-%d")
    if_first_episode = current_episode == 1
    if_last_episode = current_episode == total_episodes
    start_date, finish_date = "", ""

    if watch_status:
        start_date = (
            watch_status.start_date.strftime("%Y-%m-%d")
            if watch_status.start_date
            else ""
        )
        finish_date = (
            watch_status.finish_date.strftime("%Y-%m-%d")
            if watch_status.finish_date
            else ""
        )

        if watch_status.is_rewatching:
            return "", ""

    if not start_date and if_first_episode:
        start_date = today

    if not finish_date and if_last_episode:
        finish_date = today
    return start_date, finish_date
