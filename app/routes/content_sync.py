import urllib.parse
from typing import Optional, Tuple

from flask import Blueprint
from requests import HTTPError

from app.db.db import get_mal_id_from_kitsu_id
from app.routes import mal_client, MAL_ID_PREFIX
from app.routes.auth import get_token
from app.routes.manifest import MANIFEST
from app.routes.utils import respond_with, log_error

content_sync_bp = Blueprint('content_sync', __name__)


class Status:
    """Enumeration for update status"""
    OK = "MAL=OK"
    NULL = "MAL=NO_UPDATE"
    SKIP = "MAL=SKIPPED"
    INVALID_ID = "MAL=INVALID_ID"
    NOT_LIST = "MAL=NOT_LISTED"
    FAIL = "MAL=FAIL"


def _handle_content_id(content_id):
    """
    Extract the ID of the content and the current episode.
    If ID is a Kitsu ID, get the relevant MAL ID from the database.
    :param content_id: The content ID
    :return: The ID of the content and the current episode
    """
    if content_id.startswith(MAL_ID_PREFIX):
        return content_id.replace(f"{MAL_ID_PREFIX}_", ''), 1  # Assume episode
    elif content_id.startswith('kitsu:'):
        content_id = content_id.replace('kitsu:', '')
        current_episode = 1

        if content_id.count(':') == 1:  # Handle series
            content_id, current_episode = content_id.split(':')

        exists, mal_id = get_mal_id_from_kitsu_id(content_id)
        if exists:
            return mal_id, int(current_episode)
    return None, -1


def _get_anime_status(token, mal_id):
    """
    Get the total number of episodes and the watched status of an anime from MyAnimeList.
    :param token: The user's access token
    :param mal_id: The ID of the anime
    :return: A tuple of (total_episodes, list_status)
    """
    resp = mal_client.get_anime_details(token, mal_id, fields='num_episodes my_list_status')
    total_episodes = resp.get('num_episodes', 0)
    list_status = resp.get('my_list_status', None)
    return total_episodes, list_status


@content_sync_bp.route('/<user_id>/subtitles/<content_type>/<content_id>/<video_hash>.json')
@content_sync_bp.route('/<user_id>/subtitles/<content_type>/<content_id>.json')
def addon_content_sync(user_id: str, content_type: str, content_id: str, video_hash: str = None):
    """
    Synchronize watched status for a specific content with MyAnimeList.
    Stremio will call this endpoint when a user watches a video, requesting a subtitle for it.
    The addon will assume the user has watched the content and will update the watched status in MyAnimeList.
    :param user_id: The user's API token for MyAnimeList
    :param content_type: The type of content
    :param content_id: The ID of the content
    :param video_hash: The hash of the video (ignored)
    :return: JSON response
    """
    content_id = urllib.parse.unquote(content_id)
    if content_type not in MANIFEST['types']:
        return respond_with(
            {'subtitles': [{'id': 1, 'url': 'about:blank', 'lang': Status.SKIP}], 'message': 'Content not supported'})

    mal_id, current_episode = _handle_content_id(content_id)
    if not mal_id:
        return respond_with(
            {'subtitles': [{'id': 1, 'url': 'about:blank', 'lang': Status.INVALID_ID}], 'message': 'Invalid ID'})

    try:
        token = get_token(user_id)
        total_episodes, list_status = _get_anime_status(token, mal_id)
        if not list_status:
            return respond_with({'subtitles': [{'id': 1, 'url': 'about:blank', 'lang': Status.NOT_LIST}],
                                 'message': 'Content not in a watchlist'})

        current_status = list_status.get('status', None)
        watched_episodes = list_status.get('num_episodes_watched', 0)
        status, episode = handle_current_status(current_status, current_episode, watched_episodes, total_episodes)
        if status is None:
            return respond_with(
                {'subtitles': [{'id': 1, 'url': 'about:blank', 'lang': Status.NULL}], 'message': 'No update required'})

        mal_client.update_watched_status(token, mal_id, current_episode, status)
        return respond_with(
            {'subtitles': [{'id': 1, 'url': 'about:blank', 'lang': Status.OK}], 'message': 'Content updated'})
    except HTTPError as err:
        log_error(err)
        return respond_with({'subtitles': [{'id': 1, 'url': 'about:blank', 'lang': Status.FAIL}],
                             'message': 'Failed to update content'})


def handle_current_status(status, current_episode, watched_episodes, total_episodes) -> Tuple[Optional[str], int]:
    """
    Handle the current status of the anime in user's watchlists.
    :param status: The current watchlist status that the anime is in
    :param current_episode: The current episode being watched by the user
    :param watched_episodes: The number of episodes the user has watched
    :param total_episodes: The total number of episodes the anime has
    :return: A tuple of (status, episode)
    """
    if status in {"watching", "plan_to_watch", "on_hold"}:
        if current_episode == total_episodes:
            return "completed", total_episodes
        elif current_episode > watched_episodes:
            return "watching", current_episode

    return None, -1
