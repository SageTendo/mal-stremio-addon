import ast
import os
import re
import urllib.parse
from typing import Optional, cast, get_args

import aiohttp
from mal import (
    MEDIA_TYPE,
    SEASONAL_LIST_SORT,
    SEASONS,
    USER_ANIME_STATUS,
    USER_LIST_SORT,
    Anime,
    Auth,
    Client,
    User,
    WatchStatus,
)

import config
from app.lib.content_sync import (
    UpdateStatus,
    determine_watch_dates,
    handle_current_status,
)
from app.lib.metadata import parse_background, to_stremio_genres
from app.routes import manifest
from config import Config

MAL_CALLBACK_URL = f"{Config.PROTOCOL}://{Config.REDIRECT_URL}/callback"
MAL_CLIENT_ID = os.environ.get("MAL_ID")
MAL_CLIENT_SECRET = os.environ.get("MAL_SECRET")


class MalService:
    def __init__(self):
        self._client: Optional[Client] = None

    async def start(self):
        if self._client:
            return self

        self._client = Client(
            client_id=MAL_CLIENT_ID,
            client_secret=MAL_CLIENT_SECRET,
            callback_url=MAL_CALLBACK_URL,
            session=aiohttp.ClientSession(),
        )

        if not self._client:
            raise RuntimeError("MAL client not initialized")
        return self

    async def stop(self):
        if self._client:
            await self._client.close()

    def get_auth(self):
        if not self._client:
            raise RuntimeError("MAL client not initialized")
        return self._client.get_auth()

    async def get_access_token(self, code: str, code_verifier: str) -> Auth:
        if not self._client:
            raise RuntimeError("MAL client not initialized")
        return await self._client.get_access_token(code, code_verifier)

    async def refresh_token(self, refresh_token: str) -> Auth:
        if not self._client:
            raise RuntimeError("MAL client not initialized")
        return await self._client.refresh_token(refresh_token)

    async def get_user_details(self, token: str) -> User:
        if not self._client:
            raise RuntimeError("MAL client not initialized")
        return await self._client.get_user_details(token=token)

    async def search_anime(
        self,
        *,
        query: str,
        limit: int = 100,
        offset: int = 0,
        nsfw: bool = False,
    ) -> list[Anime]:
        if not self._client:
            raise RuntimeError("MAL client not initialized")

        if query and len(query) < 3:
            raise ValueError("Search query must be at least 3 characters long")

        return await self._client.search_anime(
            query=query, limit=limit, offset=offset, nsfw=nsfw
        )

    async def get_user_anime_list(
        self,
        *,
        token: str,
        limit: int = 100,
        offset: int = 0,
        sort: str = "list_updated_at",
        status: str = "plan_to_watch",
        nsfw: bool = False,
    ) -> list[Anime]:
        if not self._client:
            raise RuntimeError("MAL client not initialized")

        sort = cast(USER_LIST_SORT, sort)
        if sort not in get_args(USER_LIST_SORT):
            raise ValueError("Invalid sort value")

        status = cast(USER_ANIME_STATUS, status)
        if status not in get_args(USER_ANIME_STATUS):
            raise ValueError("Invalid status value")

        return await self._client.get_user_anime_list(
            token=token,
            limit=limit,
            offset=offset,
            sort=sort,
            status=status,
            nsfw=nsfw,
        )

    async def get_seasonal_anime_list(
        self,
        *,
        token: str,
        limit: int = 100,
        offset: int = 0,
        sort: str = "list_updated_at",
        nsfw: bool = False,
        year: int = 2026,
        season: str = "summer",
    ) -> list[Anime]:
        if not self._client:
            raise RuntimeError("MAL client not initialized")

        sort = cast(SEASONAL_LIST_SORT, sort)
        if sort not in get_args(SEASONAL_LIST_SORT):
            raise ValueError("Invalid sort value")

        season = season.lower()
        season = cast(SEASONS, season)
        if season not in get_args(SEASONS):
            raise ValueError("Invalid season value")

        return await self._client.get_seasonal_anime_list(
            token=token,
            year=year,
            season=season,
            limit=limit,
            offset=offset,
            sort=sort,
            nsfw=nsfw,
        )

    async def get_anime_details(self, *, anime_id: str, token: str = "") -> Anime:
        if not self._client:
            raise RuntimeError("MAL client not initialized")

        anime_id = re.sub(r"[^0-9]", "", str(anime_id))
        return await self._client.get_anime_details(
            token=token,
            anime_id=anime_id,
        )

    async def update_watch_status(
        self,
        *,
        token: str,
        anime_id: str,
        episode: int,
        status: USER_ANIME_STATUS,
        start_date: str = "",
        finish_date: str = "",
    ) -> WatchStatus:
        if not self._client:
            raise RuntimeError("MAL client not initialized")

        return await self._client.update_watch_status(
            token=token,
            anime_id=anime_id,
            episode=episode,
            status=status,
            start_date=start_date,
            finish_date=finish_date,
        )

    async def sync_anime_status(
        self,
        *,
        token: str,
        anime_id: str,
        episode: int,
        sync_unlisted: bool = False,
    ) -> UpdateStatus:
        """
        Synchronize watched status for a specific anime with MyAnimeList.
        :param token: The user's access token
        :param anime_id: The ID of the anime
        :param episode: The current episode
        :param sync_unlisted: Whether to sync unlisted anime
        :return: UpdateStatus
        """
        if not self._client:
            raise RuntimeError("MAL client not initialized")

        anime = await self.get_anime_details(anime_id=anime_id, token=token)
        total_episodes = anime.num_episodes or 0
        num_episodes_watched = (
            anime.my_list_status.num_episodes_watched if anime.my_list_status else 0
        )

        current_watch_status = str(
            anime.my_list_status.status if anime.my_list_status else ""
        )

        if not sync_unlisted and not current_watch_status:
            return UpdateStatus.NOT_LIST

        if sync_unlisted and not current_watch_status:
            # Treat unlisted anime as watching if user wants it tracked
            current_watch_status = "watching"

        new_watch_status = handle_current_status(
            current_watch_status, episode, num_episodes_watched, total_episodes
        )
        new_watch_status = cast(USER_ANIME_STATUS, new_watch_status)
        if not new_watch_status:
            return UpdateStatus.NULL

        start_date, finish_date = determine_watch_dates(
            anime.my_list_status, episode, total_episodes
        )

        await self.update_watch_status(
            token=token,
            anime_id=anime_id,
            episode=episode,
            status=new_watch_status,
            start_date=start_date,
            finish_date=finish_date,
        )
        return UpdateStatus.OK

    def filter_anime(self, anime_list: list[Anime], genre: str = "") -> list[Anime]:
        if not genre:
            return anime_list
        return list(filter(lambda x: self._has_genre_tag(x, genre), anime_list))

    @staticmethod
    def _has_genre_tag(anime: Anime, genre: str = ""):
        decoded = urllib.parse.unquote(genre)

        try:
            if decoded.startswith("{") and decoded.endswith("}"):
                formatted = ast.literal_eval(decoded).get("name", decoded)
            else:
                formatted = decoded
        except (ValueError, SyntaxError):
            formatted = decoded

        return any(g and g.lower() == formatted.lower() for g in anime.genres)

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

        genres = [g for g in anime.genres if g and g in manifest.genres]
        stremio_genres, stremio_links = to_stremio_genres(
            genres,
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
            "genres": stremio_genres,
            "links": stremio_links,
            "poster": poster,
            "background": background if background else poster,
            "imdbRating": mean_score,
            "releaseInfo": start_date,
            "description": synopsis,
        }
