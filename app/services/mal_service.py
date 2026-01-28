import ast
import asyncio
import os
import re
import urllib.parse
from typing import Optional

import aiohttp
from mal import (
    USER_ANIME_STATUS,
    USER_LIST_SORT,
    Anime,
    Auth,
    Client,
    User,
    WatchStatus,
)

from app.lib.metadata import mal_to_meta
from config import Config

MAL_CALLBACK_URL = f"{Config.PROTOCOL}://{Config.REDIRECT_URL}/callback"
MAL_CLIENT_ID = os.environ.get("MAL_ID")
MAL_CLIENT_SECRET = os.environ.get("MAL_SECRET")


class MalService:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.client: Optional[Client] = None

    async def start(self):
        if self.client:
            return self

        async with self._lock:
            if self.client:
                return self

            self.client = Client(
                client_id=MAL_CLIENT_ID,
                client_secret=MAL_CLIENT_SECRET,
                callback_url=MAL_CALLBACK_URL,
                session=aiohttp.ClientSession(),
            )

        if not self.client:
            raise RuntimeError("MAL client not initialized")
        return self

    async def stop(self):
        if self.client:
            await self.client.close()

    def get_auth(self):
        if not self.client:
            raise RuntimeError("MAL client not initialized")
        return self.client.get_auth()

    async def get_access_token(self, code: str, code_verifier: str) -> Auth:
        assert self.client is not None, "MAL Client not initialized"
        return await self.client.get_access_token(code, code_verifier)

    async def refresh_token(self, refresh_token: str) -> Auth:
        assert self.client is not None, "MAL Client not initialized"
        return await self.client.refresh_token(refresh_token)

    async def get_user_details(self, token: str) -> User:
        assert self.client is not None, "MAL Client not initialized"
        return await self.client.get_user_details(token=token)

    async def search_anime(
        self,
        *,
        query: str,
        limit: int = 100,
        offset: int = 0,
        nsfw: bool = False,
    ) -> list[Anime]:
        assert self.client is not None, "MAL Client not initialized"

        if query and len(query) < 3:
            raise ValueError("Search query must be at least 3 characters long")

        return await self.client.search_anime(
            query=query, limit=limit, offset=offset, nsfw=nsfw
        )

    async def get_user_anime_list(
        self,
        *,
        token: str,
        limit: int = 100,
        offset: int = 0,
        sort: USER_LIST_SORT = "list_updated_at",
        status: USER_ANIME_STATUS = "plan_to_watch",
        nsfw: bool = False,
    ) -> list[Anime]:
        assert self.client is not None, "MAL Client not initialized"
        return await self.client.get_user_anime_list(
            token=token,
            limit=limit,
            offset=offset,
            sort=sort,
            status=status,
            nsfw=nsfw,
        )

    async def get_anime_details(self, token: str, anime_id: str) -> Anime:
        assert self.client is not None, "MAL Client not initialized"
        return await self.client.get_anime_details(
            token=token,
            anime_id=anime_id,
        )

    async def update_watched_status(
        self,
        token: str,
        anime_id: str,
        episode: int,
        status: USER_ANIME_STATUS = "watching",
        start_date: str = "",
        finish_date: str = "",
    ) -> WatchStatus:
        assert self.client is not None, "MAL Client not initialized"
        return await self.client.update_watch_status(
            token=token,
            anime_id=anime_id,
            episode=episode,
            status=status,
            start_date=start_date,
            finish_date=finish_date,
        )

    def filter_anime(self, anime_list: list[Anime], genre: str = "") -> list[Anime]:
        if not genre:
            return anime_list
        return list(filter(lambda x: self._has_genre_tag(x, genre), anime_list))

    @staticmethod
    def _has_genre_tag(anime: Anime, genre: str = ""):
        decoded_string = urllib.parse.unquote(genre)
        if re.search(r"\{.*}", decoded_string):
            formatted_genre = ast.literal_eval(decoded_string)["name"]
        else:
            formatted_genre = genre

        return any(formatted_genre.lower() == genre.lower() for genre in anime.genres)

    def to_stremio_meta(
        self,
        *,
        anime: Anime,
        catalog_type: str = "anime",
        catalog_id: str = "plan_to_watch",
        transport_url: str = "",
    ):
        return mal_to_meta(
            anime,
            catalog_type=catalog_type,
            catalog_id=catalog_id,
            transport_url=transport_url,
        )

    def to_stremio_metas(
        self,
        *,
        anime_list: list[Anime],
        catalog_type: str = "anime",
        catalog_id: str = "plan_to_watch",
        transport_url: str = "",
    ):
        return [
            mal_to_meta(
                anime=anime,
                catalog_type=catalog_type,
                catalog_id=catalog_id,
                transport_url=transport_url,
            )
            for anime in anime_list
        ]
