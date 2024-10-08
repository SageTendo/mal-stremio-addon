import logging
import urllib.parse

import httpx
from flask import Blueprint, abort
from requests import HTTPError

from app.routes import IMDB_ID_PREFIX, mal_client, MAL_ID_PREFIX
from app.routes.catalog import get_token
from app.routes.manifest import MANIFEST
from app.routes.utils import respond_with, log_error

content_sync_bp = Blueprint('content_sync', __name__)
haglund_API = "https://arm.haglund.dev/api/v2/ids"


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
    mal_id = ""
    current_episode = 1

    content_id = urllib.parse.unquote(content_id)
    if (IMDB_ID_PREFIX in content_id) or (content_type not in MANIFEST['types']):
        return respond_with({'subtitles': []})

    if content_id.startswith('kitsu:'):

        content_id = content_id.replace('kitsu:', '')
        if content_id.count(':') == 0:  # Handle movie
            anime_id = content_id
        else:  # Handle episode
            anime_id, current_episode = content_id.split(':')
            current_episode = int(current_episode)

        # Fetch MyAnimeList ID from mapper
        resp = httpx.get(haglund_API, params={'source': 'kitsu', 'id': int(anime_id)})
        if resp.status_code >= 400:
            logging.error(resp.status_code, resp.reason_phrase)
            abort(404)

        mal_id = resp.json().get('myanimelist', None)
        if mal_id is None:
            logging.warning("No id for MyAnimeList found")
            abort(404)

    elif content_id.startswith(MAL_ID_PREFIX):
        mal_id = content_id.replace(f"{MAL_ID_PREFIX}_", '')

    # Get anime details
    token = get_token(user_id)
    resp = mal_client.get_anime_details(token, mal_id, fields='num_episodes my_list_status')
    total_episodes = resp.get('num_episodes', 0)
    current_status = resp.get('my_list_status', {}).get('status', None)
    watched_episodes = resp.get('my_list_status', {}).get('num_episodes_watched', 0)

    # Update watched status in MyAnimeList
    status, episode = handle_current_status(current_status, current_episode, watched_episodes, total_episodes)
    if status is None:
        return respond_with({'subtitles': [], 'message': 'Nothing to update'})

    try:
        mal_client.update_watched_status(token, mal_id, current_episode, status)
    except HTTPError as err:
        log_error(err)
        return respond_with({'subtitles': [], 'message': 'Failed to update watched status'})
    return respond_with({'subtitles': [], 'message': 'Updated watched status'})


def handle_current_status(status, current_episode, watched_episodes, total_episodes):
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
        if current_episode > watched_episodes:
            return "watching", current_episode

    return None, -1
