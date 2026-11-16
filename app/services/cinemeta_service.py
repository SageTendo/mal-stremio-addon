import asyncio
from typing import Optional

import aiohttp

import config
from app.services.db import get_cache, set_cache


class CinemetaService:
    def __init__(self):
        self._client: Optional[aiohttp.ClientSession] = None

    async def start(self):
        if self._client:
            return self
        self._client = aiohttp.ClientSession()
        return self

    async def stop(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def get_season_episode_videos(self, imdb_id: str) -> Optional[list[dict]]:
        """
        Fetch an IMDB title's per-episode season/episode data from Cinemeta,
        cached by IMDB id via the DB backend. Returns None if the title isn't
        cached and the live call fails/times out, so callers can fall back to
        the flat-offset approximation.
        """
        cache_key = f"cinemeta:{imdb_id}"
        cached = get_cache(cache_key)
        if cached is not None:
            return cached.get("videos")

        if not self._client:
            return None

        try:
            async with self._client.get(
                f"{config.CINEMETA_BASE_URL}/meta/series/{imdb_id}.json",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status != 200:
                    return None
                data = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

        videos = (data.get("meta") or {}).get("videos") or []
        set_cache(cache_key, {"videos": videos}, config.CINEMETA_CACHE_TTL)
        return videos


def compute_per_season_counts(
    *,
    videos: list[dict],
    from_season: int,
    from_episode: int,
    next_from_season: Optional[int] = None,
) -> list[int]:
    """Real per-season episode counts for the season range owned by one
    Kitsu/MAL entry, from Cinemeta's videos list for the shared IMDB title."""
    counts: list[int] = []
    for video in videos:
        season = video.get("season")
        episode = video.get("episode")
        if episode is None:
            episode = video.get("number")
        if not isinstance(season, int) or not isinstance(episode, int):
            continue
        if season < from_season:
            continue
        if season == from_season and episode < from_episode:
            continue
        if next_from_season is not None and season >= next_from_season:
            continue

        index = season - from_season
        while len(counts) <= index:
            counts.append(0)
        counts[index] += 1
    return counts


def place_episode(
    *,
    from_season: int,
    from_episode: int,
    per_season_counts: list[int],
    non_imdb_episodes: frozenset,
    absolute_episode: int,
) -> Optional[tuple[int, int]]:
    """Place an absolute (Kitsu/MAL-numbered) episode into its correct IMDB
    season/episode using real per-season counts, skipping episodes that don't
    correspond to any IMDB-tracked episode. Returns None when there's nothing
    to place it against (no counts, the episode itself is untracked, or it
    falls beyond every known Cinemeta episode) — callers fall back to the
    flat-offset approximation in that case."""
    if not per_season_counts:
        return None
    if absolute_episode in non_imdb_episodes:
        return None

    skipped = sum(1 for ep in non_imdb_episodes if ep < absolute_episode)
    adjusted = absolute_episode - skipped
    if adjusted < 1:
        return None

    cumulative = 0
    season_index = None
    for i, count in enumerate(per_season_counts):
        cumulative += count
        if cumulative >= adjusted:
            season_index = i
            break

    if season_index is None:
        return None

    previous_seasons_count = sum(per_season_counts[:season_index])
    season = from_season + season_index
    episode = from_episode - 1 + adjusted - previous_seasons_count
    return season, episode


def _invert_skip_offset(adjusted: int, non_imdb_episodes: frozenset) -> int:
    absolute_episode = adjusted
    while True:
        skip_count = sum(1 for ep in non_imdb_episodes if ep <= absolute_episode)
        new_value = adjusted + skip_count
        if new_value == absolute_episode:
            return new_value
        absolute_episode = new_value


def unplace_episode(
    *,
    from_season: int,
    from_episode: int,
    per_season_counts: list[int],
    non_imdb_episodes: frozenset,
    season: int,
    episode: int,
) -> Optional[int]:
    """Inverse of place_episode: given a real IMDB season/episode, recover the
    absolute (Kitsu/MAL-numbered) episode number."""
    if not per_season_counts:
        return None

    season_index = season - from_season
    if season_index < 0 or season_index >= len(per_season_counts):
        return None

    previous_seasons_count = sum(per_season_counts[:season_index])
    adjusted = episode - from_episode + 1 + previous_seasons_count
    if adjusted < 1:
        return None

    return _invert_skip_offset(adjusted, non_imdb_episodes)
