import ast
import asyncio
import os
import re
import urllib.parse
from typing import Optional

import aiohttp
from mal import (
    MEDIA_TYPE,
    USER_ANIME_STATUS,
    USER_LIST_SORT,
    Anime,
    Auth,
    Client,
    User,
    WatchStatus,
)

import config
from app.lib.metadata import parse_background, parse_genres
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
        """
        Convert MAL anime item to a valid Stremio meta format
        :param anime: The MAL anime item to convert
        :param catalog_type: The type of catalog being referenced in the link meta object
        :param catalog_id: The id of catalog being referenced in the link meta object
        :param transport_url: The url to the addon's manifest.json
        :return: Stremio meta format
        """

        formatted_content_id = None
        if content_id := anime.id:
            formatted_content_id = f"{config.MAL_ID_PREFIX}{content_id}"

        title = anime.title.english or anime.title.canonical
        synopsis = anime.synopsis
        poster = anime.main_picture() or anime.main_picture("medium")

        genres, links = parse_genres(
            anime.genres,
            transport_url,
            catalog_type,
            catalog_id,
        )

        mean_score: Optional[str] = None
        if score := anime.mean:
            mean_score = str(score)

        start_date: Optional[str] = None
        if anime.start_date:
            start_date = str(anime.start_date.year)
            start_date += "-"

            if anime.end_date:
                start_date += str(anime.end_date.year)

        picture_objects = anime.pictures("large") or anime.pictures("medium")
        background = parse_background(picture_objects)

        valid_series_types: list[MEDIA_TYPE] = [
            "tv",
            "ona",
            "ova",
            "special",
            "unknown",
            "music",
        ]
        media_type: Optional[str] = None
        if anime.media_type:
            if anime.media_type.lower() in valid_series_types:
                media_type = "series"
            elif anime.media_type.lower() == "movie":
                media_type = "movie"

        return {
            "id": formatted_content_id,
            "name": title,
            "type": media_type,
            "genres": genres,
            "links": links,
            "poster": poster,
            "background": background if background else poster,
            "imdbRating": mean_score,
            "releaseInfo": start_date,
            "description": synopsis,
        }
