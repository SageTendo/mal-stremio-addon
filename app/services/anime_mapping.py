import json
import re

from app.routes.utils import log_error
from config import ANIME_MAPPING_JSON

_mal_to_kitsu: dict[int, int] = {}
_kitsu_to_mal: dict[int, int] = {}
_loaded = False


def load_mapping_db() -> None:
    global _mal_to_kitsu, _kitsu_to_mal, _loaded

    if _loaded:
        return

    try:
        with open(ANIME_MAPPING_JSON) as f:
            data = json.load(f)

        mal_to_kitsu: dict[int, int] = {}
        kitsu_to_mal: dict[int, int] = {}
        for entry in data:
            mal_id = entry.get("mal_id")
            kitsu_id = entry.get("kitsu_id")
            if mal_id and kitsu_id:
                mal_to_kitsu[int(mal_id)] = int(kitsu_id)
                kitsu_to_mal[int(kitsu_id)] = int(mal_id)

        _mal_to_kitsu = mal_to_kitsu
        _kitsu_to_mal = kitsu_to_mal
        _loaded = True
    except Exception as e:
        log_error(
            "MAPPING_ERROR",
            str(e),
            f"Check and make sure the mapping database: {ANIME_MAPPING_JSON} exists and is a valid JSON file",
        )


def get_kitsu_id_from_mal_id(mal_id) -> tuple[bool, str]:
    mal_id = re.sub(r"[^0-9]", "", str(mal_id))
    try:
        mal_id_int = int(mal_id)
        if kitsu_id := _mal_to_kitsu.get(mal_id_int):
            return True, str(kitsu_id)
    except ValueError:
        log_error("VALUE ERROR", f"Invalid MAL ID: {mal_id}", "Invalid MAL ID")
    return False, ""


def get_mal_id_from_kitsu_id(kitsu_id) -> tuple[bool, str]:
    kitsu_id = re.sub(r"[^0-9]", "", str(kitsu_id))
    try:
        kitsu_id_int = int(kitsu_id)
        if mal_id := _kitsu_to_mal.get(kitsu_id_int):
            return True, str(mal_id)
    except ValueError:
        log_error("VALUE ERROR", f"Invalid Kitsu ID: {kitsu_id}", "Invalid Kitsu ID")
    return False, ""
