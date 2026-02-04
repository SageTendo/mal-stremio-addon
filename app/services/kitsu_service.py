import asyncio
import os
import re
from math import ceil
from typing import Optional

import kitsu
import Levenshtein

KITSU_CLIENT_ID = os.environ.get("KITSU_ID")
KITSU_CLIENT_SECRET = os.environ.get("KITSU_SECRET")


class KitsuService:
    def __init__(self):
        self.client: Optional[kitsu.Client] = None
        self._lock = asyncio.Lock()

    async def start(self):
        if self.client:
            return self

        self.client = kitsu.Client(
            client_id=KITSU_CLIENT_ID, client_secret=KITSU_CLIENT_SECRET
        )

        if not self.client:
            raise RuntimeError("Kitsu client not initialized")
        return self

    async def stop(self):
        if self.client:
            await self.client.close()
            self.client = None

    async def get_anime_by_id(
        self, kitsu_id: str, *, include_nsfw: bool = False
    ) -> Optional[kitsu.Anime]:
        if not self.client:
            raise RuntimeError("Kitsu client not initialized")

        kitsu_id = re.sub(r"[^0-9]", "", str(kitsu_id))
        if not kitsu_id.isdigit():
            raise ValueError("Invalid Kitsu ID")
        return await self.client.get_anime(int(kitsu_id), include_nsfw=include_nsfw)

    async def get_anime_by_title(
        self, query: str, *, include_nsfw: bool = False
    ) -> Optional[kitsu.Anime]:
        if not self.client:
            raise RuntimeError("Kitsu client not initialized")

        results = await self.client.search_anime(
            query, include_nsfw=include_nsfw, limit=20
        )
        if not results:
            return None

        if len(results) == 1:
            return results[0]
        return self._best_match_by_title(results, query)

    async def get_video_metadata(self, anime: kitsu.Anime) -> list[dict]:
        if anime.subtype == "movie":
            return []

        episode_count = anime.episode_count or (
            ceil(anime.total_length / anime.episode_length)
            if anime.total_length and anime.episode_length
            else 0
        )

        return [
            await self._populate_video_metadata(anime, episode)
            for episode in range(1, episode_count + 1)
        ]

    def _best_match_by_title(
        self, results: list[kitsu.Anime], query: str
    ) -> kitsu.Anime:
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

    async def _populate_video_metadata(self, anime: kitsu.Anime, episode: int) -> dict:
        return {
            "id": f"kitsu:{anime.id}:{episode}",
            "title": f"Episode {episode}",
            "thumbnail": anime.cover_image("tiny"),
            "available": True,
            "episode": episode,
            "season": 1,
        }
