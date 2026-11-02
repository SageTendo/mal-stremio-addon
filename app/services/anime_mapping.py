import json
import re
from dataclasses import dataclass, field
from typing import Optional

import config
from app.routes.utils import log_error
from config import ANIME_MAPPING_JSON, IMDB_MAPPING_JSON

PRIORITY = ("imdb", "tvdb", "tmdb")


@dataclass(frozen=True)
class MappingEntry:
    identifier_type: str
    identifier: str
    mal_id: Optional[int] = None
    kitsu_id: Optional[int] = None
    from_season: int = 1
    from_episode: int = 1
    non_imdb_episodes: frozenset = field(default_factory=frozenset)


@dataclass(frozen=True)
class ResolvedMapping:
    """The best available Cinemeta-compatible id for a title, plus enough
    context (from_season/from_episode/non_imdb_episodes/next_from_season) to
    place any of its absolute (Kitsu/MAL-numbered) episodes into a season and
    in-season episode number."""

    source: str  # "imdb" | "tvdb" | "tmdb" | "kitsu" | "mal"
    identifier: str
    from_season: int = 1
    from_episode: int = 1
    non_imdb_episodes: frozenset = field(default_factory=frozenset)
    next_from_season: Optional[int] = None


@dataclass(frozen=True)
class InboundResolution:
    """The result of resolving an incoming Cinemeta-style id (+ season/episode)
    back to a MAL id, plus enough context to refine the absolute episode number
    with real per-season Cinemeta data."""

    mal_id: str
    flat_absolute_episode: int
    source: str
    identifier: str
    from_season: int
    from_episode: int
    non_imdb_episodes: frozenset
    next_from_season: Optional[int] = None


# anime-list-mini.json (MAL-keyed, Fribb)
_mal_to_kitsu: dict[int, int] = {}
_kitsu_to_mal: dict[int, int] = {}
_mal_forward: dict[int, dict[str, MappingEntry]] = {}
_mal_reverse: dict[str, dict[str, list[MappingEntry]]] = {t: {} for t in PRIORITY}

# imdb_mapping.json (Kitsu-keyed, TheBeastLT)
_kitsu_forward: dict[int, dict[str, MappingEntry]] = {}
_kitsu_reverse: dict[str, dict[str, list[MappingEntry]]] = {t: {} for t in PRIORITY}

_loaded = False


def _load_mal_source(path):
    mal_to_kitsu: dict[int, int] = {}
    kitsu_to_mal: dict[int, int] = {}
    forward: dict[int, dict[str, MappingEntry]] = {}
    reverse: dict[str, dict[str, list[MappingEntry]]] = {t: {} for t in PRIORITY}

    with open(path) as f:
        data = json.load(f)

    for entry in data:
        mal_id = entry.get("mal_id")
        if not mal_id:
            continue
        mal_id = int(mal_id)

        kitsu_id = entry.get("kitsu_id")
        if kitsu_id:
            kitsu_id = int(kitsu_id)
            mal_to_kitsu[mal_id] = kitsu_id
            kitsu_to_mal[kitsu_id] = mal_id

        imdb_ids = entry.get("imdb_id") or []
        imdb_id = imdb_ids[0] if imdb_ids else None

        tvdb_id = entry.get("tvdb_id")

        tmdb_raw = entry.get("themoviedb_id") or {}
        tmdb_id = tmdb_raw.get("movie") or tmdb_raw.get("tv")
        if isinstance(tmdb_id, list):
            tmdb_id = tmdb_id[0] if tmdb_id else None

        season_raw = entry.get("season") or {}
        from_season = season_raw.get("tvdb")
        if from_season is None:
            from_season = season_raw.get("tmdb")
        if not isinstance(from_season, int):
            from_season = 1

        ids = {"imdb": imdb_id, "tvdb": tvdb_id, "tmdb": tmdb_id}

        entries = {}
        for id_type in PRIORITY:
            value = ids.get(id_type)
            if not value:
                continue

            mapping_entry = MappingEntry(
                identifier_type=id_type,
                identifier=str(value),
                mal_id=mal_id,
                kitsu_id=kitsu_id,
                from_season=from_season,
                from_episode=1,
            )
            entries[id_type] = mapping_entry
            reverse[id_type].setdefault(str(value), []).append(mapping_entry)

        if entries:
            forward[mal_id] = entries

    return mal_to_kitsu, kitsu_to_mal, forward, reverse


def _load_kitsu_source(path):
    forward: dict[int, dict[str, MappingEntry]] = {}
    reverse: dict[str, dict[str, list[MappingEntry]]] = {t: {} for t in PRIORITY}

    with open(path) as f:
        data = json.load(f)

    for entry in data:
        kitsu_id = entry.get("kitsu_id")
        if kitsu_id is None:
            continue
        kitsu_id = int(kitsu_id)

        from_season = entry.get("fromSeason")
        from_season = from_season if isinstance(from_season, int) else 1

        from_episode = entry.get("fromEpisode")
        from_episode = from_episode if isinstance(from_episode, int) else 1

        non_imdb_episodes = frozenset(entry.get("nonImdbEpisodes") or [])

        ids = {
            "imdb": entry.get("imdb_id"),
            # upstream data has been observed using both key namings for TVDB
            "tvdb": entry.get("tvdb_id") or entry.get("tvdbId"),
            "tmdb": entry.get("tmdb_id") or entry.get("tmdbId"),
        }

        entries = {}
        for id_type in PRIORITY:
            value = ids.get(id_type)
            if not value:
                continue

            mapping_entry = MappingEntry(
                identifier_type=id_type,
                identifier=str(value),
                kitsu_id=kitsu_id,
                from_season=from_season,
                from_episode=from_episode,
                non_imdb_episodes=non_imdb_episodes,
            )
            entries[id_type] = mapping_entry
            reverse[id_type].setdefault(str(value), []).append(mapping_entry)

        if entries:
            forward[kitsu_id] = entries

    return forward, reverse


def _log_mapping_load_error(e: Exception) -> None:
    if isinstance(e, FileNotFoundError):
        log_error(
            "MAPPING_ERROR",
            str(e),
            f"Check and make sure the mapping database: {e.filename} exists and is a valid JSON file",
        )
    elif isinstance(e, json.JSONDecodeError):
        log_error(
            "JSON_ERROR",
            str(e),
            "Check and make sure the mapping database file is valid JSON",
        )
    elif isinstance(e, PermissionError):
        log_error(
            "PERMISSION_ERROR",
            str(e),
            f"Check and make sure the mapping database: {e.filename} is readable",
        )
    elif isinstance(e, UnicodeDecodeError):
        log_error(
            "UNICODE_ERROR",
            str(e),
            "Check and make sure the mapping database file is encoded in UTF-8",
        )
    else:
        log_error("UNKNOWN_ERROR", str(e), "Unknown error occurred")


def load_mapping_db() -> None:
    """
    Load both mapping sources independently — a failure loading one (e.g. a
    missing/corrupt imdb_mapping.json) must not discard the other's
    successfully-parsed data, since plain mal:/kitsu: id resolution only
    depends on the MAL-keyed source and shouldn't break because of it.
    """
    global _mal_to_kitsu, _kitsu_to_mal, _mal_forward, _mal_reverse
    global _kitsu_forward, _kitsu_reverse, _loaded

    if _loaded:
        return

    try:
        _mal_to_kitsu, _kitsu_to_mal, _mal_forward, _mal_reverse = _load_mal_source(
            ANIME_MAPPING_JSON
        )
    except Exception as e:
        _log_mapping_load_error(e)

    try:
        _kitsu_forward, _kitsu_reverse = _load_kitsu_source(IMDB_MAPPING_JSON)
    except Exception as e:
        _log_mapping_load_error(e)

    _loaded = True


def _next_season_boundary(
    siblings: list[MappingEntry], current: MappingEntry
) -> Optional[int]:
    """
    The from_season of the next entry starting a strictly later season than
    `current`, used to bound `current`'s season range for the per-season
    Cinemeta episode count. A sibling with the same from_season as `current`
    (a mid-season episode-only split, e.g. real-world "season 0" specials
    data) is not a season boundary and must not be treated as one — doing so
    would zero out `current`'s own season range entirely.
    """
    candidates = [
        e.from_season for e in siblings if e.from_season > current.from_season
    ]
    return min(candidates) if candidates else None


def _to_resolved_mapping(
    entry: MappingEntry, reverse: dict[str, list[MappingEntry]]
) -> ResolvedMapping:
    siblings = reverse.get(entry.identifier, [])
    return ResolvedMapping(
        source=entry.identifier_type,
        identifier=entry.identifier,
        from_season=entry.from_season,
        from_episode=entry.from_episode,
        non_imdb_episodes=entry.non_imdb_episodes,
        next_from_season=_next_season_boundary(siblings, entry),
    )


def resolve_outbound(
    *, mal_id: Optional[int] = None, kitsu_id: Optional[int] = None
) -> ResolvedMapping:
    """
    Resolve the best available Cinemeta-compatible id for a title, given its
    MAL id and/or Kitsu id. Checks the Kitsu-keyed mapping source first, then
    the MAL-keyed source, then falls back to a bare Kitsu id, then a MAL id.
    """
    if kitsu_id is None and mal_id is not None:
        kitsu_id = _mal_to_kitsu.get(int(mal_id))
    if mal_id is None and kitsu_id is not None:
        mal_id = _kitsu_to_mal.get(int(kitsu_id))

    if kitsu_id is not None:
        entries = _kitsu_forward.get(int(kitsu_id))
        if entries:
            for id_type in PRIORITY:
                if id_type in entries:
                    return _to_resolved_mapping(
                        entries[id_type], _kitsu_reverse[id_type]
                    )

    if mal_id is not None:
        entries = _mal_forward.get(int(mal_id))
        if entries:
            for id_type in PRIORITY:
                if id_type in entries:
                    return _to_resolved_mapping(entries[id_type], _mal_reverse[id_type])

    if kitsu_id is not None:
        return ResolvedMapping(source="kitsu", identifier=str(kitsu_id))
    if mal_id is not None:
        return ResolvedMapping(source="mal", identifier=str(mal_id))

    raise ValueError("resolve_outbound requires a mal_id or a kitsu_id")


def _select_entry(
    entries: list[MappingEntry], season: int, episode: int
) -> Optional[MappingEntry]:
    """
    Disambiguate among entries sharing one external id (a title split across
    seasons/cours) by picking the entry with the highest (from_season,
    from_episode) not exceeding the requested (season, episode).
    """
    candidates = [
        e for e in entries if (e.from_season, e.from_episode) <= (season, episode)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda e: (e.from_season, e.from_episode))


def resolve_inbound(
    *, identifier_type: str, identifier: str, season: int, episode: int
) -> Optional[InboundResolution]:
    """
    Resolve an incoming Cinemeta-style id (+ season/episode) back to a MAL id
    and an absolute (flat-offset) episode number. Checks the Kitsu-keyed
    mapping source first, then the MAL-keyed source.
    """
    kitsu_siblings = _kitsu_reverse.get(identifier_type, {}).get(identifier, [])
    entry = _select_entry(kitsu_siblings, season, episode)
    if entry is not None:
        mal_id = entry.mal_id
        if mal_id is None and entry.kitsu_id is not None:
            mal_id = _kitsu_to_mal.get(entry.kitsu_id)
        if mal_id is not None:
            return InboundResolution(
                mal_id=str(mal_id),
                flat_absolute_episode=entry.from_episode + episode - 1,
                source=identifier_type,
                identifier=identifier,
                from_season=entry.from_season,
                from_episode=entry.from_episode,
                non_imdb_episodes=entry.non_imdb_episodes,
                next_from_season=_next_season_boundary(kitsu_siblings, entry),
            )

    mal_siblings = _mal_reverse.get(identifier_type, {}).get(identifier, [])
    entry = _select_entry(mal_siblings, season, episode)
    if entry is not None and entry.mal_id is not None:
        return InboundResolution(
            mal_id=str(entry.mal_id),
            flat_absolute_episode=entry.from_episode + episode - 1,
            source=identifier_type,
            identifier=identifier,
            from_season=entry.from_season,
            from_episode=entry.from_episode,
            non_imdb_episodes=entry.non_imdb_episodes,
            next_from_season=_next_season_boundary(mal_siblings, entry),
        )

    return None


def compute_flat_season_episode(
    mapping: ResolvedMapping, absolute_episode: int
) -> tuple[int, int]:
    """Season/episode via the flat starting-episode-offset rule, with no live
    network calls involved. Used for the kitsu/mal fallback tiers, the
    TVDB/TMDB branches (Cinemeta has no equivalent data for those), and as the
    IMDB branch's fallback when a live Cinemeta call isn't available/fails."""
    return mapping.from_season, mapping.from_episode + absolute_episode - 1


def parse_cinemeta_id(
    raw_id: str,
) -> Optional[tuple[str, str, Optional[int], Optional[int]]]:
    """
    Parse a Cinemeta-style id, e.g. "tt0123456", "tt0123456:1:5", or
    "tvdb:12345:1:5", into (identifier_type, identifier, season, episode).
    season/episode are None when not present in the raw id.
    """
    parts = raw_id.split(":")

    if parts[0].startswith(config.IMDB_ID_PREFIX):
        identifier_type = "imdb"
        identifier = parts[0]
        rest = parts[1:]
    elif parts[0] in (config.TVDB_ID_PREFIX, config.TMDB_ID_PREFIX) and len(parts) >= 2:
        identifier_type = parts[0]
        identifier = parts[1]
        rest = parts[2:]
    else:
        return None

    season = int(rest[0]) if len(rest) >= 1 and rest[0].isdigit() else None
    episode = int(rest[1]) if len(rest) >= 2 and rest[1].isdigit() else None
    return identifier_type, identifier, season, episode


def format_cinemeta_id(identifier_type: str, identifier: str) -> str:
    if identifier_type == "imdb":
        return identifier
    return f"{identifier_type}:{identifier}"


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
