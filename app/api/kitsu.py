import httpx

from app.routes.utils import handle_error

BASE_URL = "https://kitsu.io/api/edge/anime/"


class Kitsu_Mapper:

    @staticmethod
    async def __extract_id(kitsu_id: int):
        """
        Extract the mal id from kitsu response
        :param kitsu_id: The kitsu id of the anime
        :return: The mapped mal id or, None if no mapping is found
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}{kitsu_id}/mappings")

        resp.raise_for_status()

        data = resp.json().get('data', [])
        for item in data:
            attributes = item.get('attributes', {})
            external_site: str = attributes.get('externalSite', '')
            external_id: str = attributes.get('externalId', None)

            if external_site.startswith('myanimelist') and external_id:
                return external_id
        return None

    @staticmethod
    async def get_mal_id(kitsu_id: int):
        try:
            return await Kitsu_Mapper.__extract_id(kitsu_id)
        except httpx.HTTPStatusError as err:
            handle_error(err)
            return None
