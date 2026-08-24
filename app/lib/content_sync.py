from datetime import date
from enum import Enum
from typing import Optional

from mal import WatchStatus

import config
from app.services.anime_mapping import (
    get_mal_id_from_kitsu_id,
    parse_cinemeta_id,
    resolve_inbound,
)
from app.services.cinemeta_service import (
    CinemetaService,
    compute_per_season_counts,
    unplace_episode,
)


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


async def handle_content_id(
    content_id: str, cinemeta_service: Optional[CinemetaService] = None
) -> tuple[Optional[str], int]:
    """
    Extract the ID of the content and the current episode.
    If ID is a Kitsu ID, get the relevant MAL ID from the database.
    If ID is a Cinemeta-style (IMDB/TVDB/TMDB) ID, resolve it back to a MAL ID
    and an absolute episode number, refining via real per-season Cinemeta
    episode counts on the IMDB branch when available.
    :param content_id: The content ID
    :param cinemeta_service: Optional Cinemeta client for real per-season episode counts
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

    parsed = parse_cinemeta_id(content_id)
    if parsed is None:
        return None, -1

    identifier_type, identifier, season, episode = parsed
    if season is None or episode is None:
        return None, -1

    resolution = resolve_inbound(
        identifier_type=identifier_type,
        identifier=identifier,
        season=season,
        episode=episode,
    )
    if resolution is None:
        return None, -1

    absolute_episode = resolution.flat_absolute_episode
    if resolution.source == "imdb" and cinemeta_service is not None:
        videos = await cinemeta_service.get_season_episode_videos(resolution.identifier)
        if videos:
            counts = compute_per_season_counts(
                videos=videos,
                from_season=resolution.from_season,
                from_episode=resolution.from_episode,
                next_from_season=resolution.next_from_season,
            )
            refined = unplace_episode(
                from_season=resolution.from_season,
                from_episode=resolution.from_episode,
                per_season_counts=counts,
                non_imdb_episodes=resolution.non_imdb_episodes,
                season=season,
                episode=episode,
            )
            if refined is not None:
                absolute_episode = refined

    return resolution.mal_id, absolute_episode


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
