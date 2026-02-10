import os
import re
from datetime import datetime
from math import ceil
from typing import Optional

import kitsu
import Levenshtein
from mal import MEDIA_TYPE

import config
from app.lib.metadata import to_stremio_genres
from app.routes import manifest

KITSU_CLIENT_ID = os.environ.get("KITSU_ID")
KITSU_CLIENT_SECRET = os.environ.get("KITSU_SECRET")


class KitsuService:
    def __init__(self):
        self._client: Optional[kitsu.Client] = None

    async def start(self):
        if self._client:
            return self

        self._client = kitsu.Client(
            client_id=KITSU_CLIENT_ID, client_secret=KITSU_CLIENT_SECRET
        )

        if not self._client:
            raise RuntimeError("Kitsu client not initialized")
        return self

    async def stop(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def get_anime_by_id(
        self, kitsu_id: str, *, include_nsfw: bool = False
    ) -> kitsu.Anime:
        if not self._client:
            raise RuntimeError("Kitsu client not initialized")

        kitsu_id = re.sub(r"[^0-9]", "", str(kitsu_id))
        if not kitsu_id.isdigit():
            raise ValueError("Invalid Kitsu ID")

        return await self._client.get_anime(
            int(kitsu_id),
            include_nsfw=include_nsfw,
            params={"include": "episodes,genres"},
        )

    async def get_anime_by_title(
        self, query: str, *, include_nsfw: bool = False
    ) -> Optional[kitsu.Anime]:
        if not self._client:
            raise RuntimeError("Kitsu client not initialized")

        results = await self._client.search_anime(
            query,
            include_nsfw=include_nsfw,
            limit=20,
            params={"include": "episodes,genres"},
        )

        if len(results) == 1:
            return results[0]
        return self._best_match_by_title(results, query)

    async def _get_video_metadata(self, anime: kitsu.Anime) -> Optional[list[dict]]:
        if anime.subtype == "movie":
            return [
                await self._populate_video_metadata(
                    video_id=f"{config.KITSU_ID_PREFIX}{anime.id}",
                    title=anime.canonical_title or anime.title or "Episode 1",
                    episode_number=1,
                    season=1,
                    thumbnail=anime.poster_image("large") or anime.poster_image(),
                    overview=anime.synopsis,
                    release=anime.start_date,
                )
            ]

        if not anime.episodes:
            episode_count = anime.episode_count or (
                ceil(anime.total_length / anime.episode_length)
                if anime.total_length and anime.episode_length
                else 0
            )

            return [
                await self._populate_video_metadata(
                    video_id=f"{config.KITSU_ID_PREFIX}{anime.id}:{episode_number}",
                    title=f"Episode {episode_number}",
                    episode_number=episode_number,
                    season=1,
                    thumbnail=anime.cover_image("tiny") or "",
                    overview="",
                    release=None,
                )
                for episode_number in range(1, episode_count + 1)
            ]

        episodes = []
        for episode in anime.episodes:
            title = (
                episode.canonical_title
                or episode.english_title
                or f"Episode {episode.number}"
            )

            episodes.append(
                await self._populate_video_metadata(
                    video_id=f"{config.KITSU_ID_PREFIX}{anime.id}:{episode.number}",
                    title=title,
                    episode_number=episode.number or 0,
                    thumbnail=episode.thumbnail,
                    overview=episode.synopsis,
                    release=episode.air_date,
                )
            )
        return episodes

    def _best_match_by_title(
        self, results: list[kitsu.Anime], query: str
    ) -> Optional[kitsu.Anime]:
        if not results:
            return None

        matching_score = 0
        matching_anime = results[0]

        for anime in results:
            english_score = Levenshtein.ratio(query, anime.title or "")
            japanese_score = Levenshtein.ratio(query, anime.japanese_title or "")
            romaji_score = Levenshtein.ratio(query, anime.romaji_title or "")
            canonical_score = Levenshtein.ratio(query, anime.canonical_title or "")
            score = max(english_score, japanese_score, canonical_score, romaji_score)

            if score > matching_score:
                matching_score = score
                matching_anime = anime
        return matching_anime

    async def _populate_video_metadata(
        self,
        *,
        video_id: str,
        title: str,
        episode_number: int,
        season: int = 1,
        thumbnail: Optional[str],
        overview: Optional[str],
        release: Optional[datetime],
    ) -> dict:
        return {
            "id": video_id,
            "title": title,
            "thumbnail": thumbnail
            or "https://episodes.metahub.space/1234/18/8/w780.jpg",
            "episode": episode_number,
            "season": season,
            "overview": overview,
            "released": release.isoformat() + "Z" if release else None,
        }

    async def to_stremio_meta(
        self,
        *,
        mal_id: str,
        anime: kitsu.Anime,
        catalog_type: str = "anime",
        catalog_id: str = "plan_to_watch",
        transport_url: str = "",
    ):
        """
        Convert kitsu anime item to a valid Stremio meta format
        :param anime: The kitsu anime item to convert
        :param catalog_type: The type of catalog being referenced in the link meta object
        :param catalog_id: The id of catalog being referenced in the link meta object
        :param transport_url: The url to the addon's manifest.json
        :return: Stremio meta format
        """
        title = anime.title or anime.canonical_title
        synopsis = anime.synopsis
        poster = anime.poster_image()

        genres = [x.name for x in anime.genres if x.name and x.name in manifest.genres]
        stremio_genres, stremio_links = to_stremio_genres(
            genres,
            transport_url,
            catalog_type,
            catalog_id,
        )

        mean_score: Optional[str] = None
        if score := anime.average_rating:
            mean_score = str(score)

        start_date: Optional[str] = None
        if anime.start_date:
            start_date = str(anime.start_date.year)
            start_date += "-"

            if anime.end_date:
                start_date += str(anime.end_date.year)

        background = anime.cover_image("large") or anime.cover_image()
        valid_series_types: list[MEDIA_TYPE] = [
            "tv",
            "ona",
            "ova",
            "special",
            "unknown",
            "music",
        ]
        media_type: Optional[str] = None
        if anime.subtype:
            if anime.subtype.lower() in valid_series_types:
                media_type = "series"
            elif anime.subtype.lower() == "movie":
                media_type = "movie"

        videos = await self._get_video_metadata(anime)
        return {
            "id": mal_id,
            "name": title,
            "type": media_type,
            "genres": stremio_genres,
            "links": stremio_links,
            "poster": poster,
            "background": background if background else poster,
            "imdbRating": mean_score,
            "releaseInfo": start_date,
            "description": synopsis,
            "videos": videos,
        }
