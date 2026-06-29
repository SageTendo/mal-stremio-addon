import json
import re

from app.routes.utils import log_error
from config import ANIME_MAPPING_JSON

_mal_to_kitsu: dict[int, int] = {}
_kitsu_to_mal: dict[int, int] = {}
_mal_to_cinemeta: dict[int, dict[str, str]] = {}
_loaded = False


def load_mapping_db() -> None:
    global _mal_to_kitsu, _kitsu_to_mal, _mal_to_cinemeta, _loaded

    if _loaded:
        return

    try:
        with open(ANIME_MAPPING_JSON) as f:
            data = json.load(f)

        mal_to_kitsu: dict[int, int] = {}
        kitsu_to_mal: dict[int, int] = {}
        mal_to_cinemeta: dict[int, dict[str, str]] = {}

        for entry in data:
            mal_id = entry.get("mal_id")
            if not mal_id:
                continue

            kitsu_id = entry.get("kitsu_id")
            if mal_id and kitsu_id:
                mal_to_kitsu[int(mal_id)] = int(kitsu_id)
                kitsu_to_mal[int(kitsu_id)] = int(mal_id)

            # Cinemeta compatible media IDs
            tvdb_id = entry.get("tvdb_id", "")
            imdb_id = entry.get("imdb_id", [])
            if imdb_id:
                imdb_id = imdb_id[0]

            tmdb_id_raw = entry.get("themoviedb_id", {})
            tmdb_id = tmdb_id_raw.get("movie") or tmdb_id_raw.get("tv")
            if isinstance(tmdb_id, list):
                tmdb_id = tmdb_id[0]

            cinemeta_ids = {}
            if imdb_id:
                cinemeta_ids["imdb"] = imdb_id
            if tvdb_id:
                cinemeta_ids["tvdb"] = tvdb_id
            if tmdb_id:
                cinemeta_ids["tmdb"] = tmdb_id

            if mal_id and cinemeta_ids:
                mal_to_cinemeta[int(mal_id)] = cinemeta_ids

        _mal_to_kitsu = mal_to_kitsu
        _kitsu_to_mal = kitsu_to_mal
        _mal_to_cinemeta = mal_to_cinemeta
        _loaded = True
    except FileNotFoundError as e:
        log_error(
            "MAPPING_ERROR",
            str(e),
            f"Check and make sure the mapping database: {ANIME_MAPPING_JSON} exists and is a valid JSON file",
        )
    except json.JSONDecodeError as e:
        log_error(
            "JSON_ERROR",
            str(e),
            f"Check and make sure the mapping database: {ANIME_MAPPING_JSON} is a valid JSON file",
        )
    except PermissionError as e:
        log_error(
            "PERMISSION_ERROR",
            str(e),
            f"Check and make sure the mapping database: {ANIME_MAPPING_JSON} is readable",
        )
    except UnicodeDecodeError as e:
        log_error(
            "UNICODE_ERROR",
            str(e),
            f"Check and make sure the mapping database: {ANIME_MAPPING_JSON} is encoded in UTF-8",
        )
    except Exception as e:
        log_error("UNKNOWN_ERROR", str(e), "Unknown error occurred")


def get_cinemeta_from_mal_id(mal_id: str) -> tuple[bool, tuple[str, str]]:
    mal_id = re.sub(r"[^0-9]", "", str(mal_id))
    try:
        mal_id_int = int(mal_id)
        ids = _mal_to_cinemeta.get(mal_id_int, {})
        for key in ("imdb", "tvdb", "tmdb"):
            if value := ids.get(key):
                return True, (key, value)
    except ValueError:
        log_error("VALUE ERROR", f"Invalid MAL ID: {mal_id}", "Invalid MAL ID")
    return False, ("", "")


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
