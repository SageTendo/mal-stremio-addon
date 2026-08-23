import json
from unittest.mock import mock_open, patch

import pytest

import app.services.anime_mapping as mapping_module
from app.services.anime_mapping import (
    format_cinemeta_id,
    get_kitsu_id_from_mal_id,
    get_mal_id_from_kitsu_id,
    load_mapping_db,
    parse_cinemeta_id,
    resolve_inbound,
    resolve_outbound,
)

_MAL_SOURCE_DATA = [
    {"mal_id": 290, "kitsu_id": 265, "type": "TV"},
    {"mal_id": 123, "kitsu_id": 14, "type": "TV"},
    {"type": "OVA"},  # entry missing both ids
    {
        "mal_id": 500,
        "kitsu_id": 501,
        "imdb_id": ["tt5000001"],
        "tvdb_id": 60001,
        "themoviedb_id": {"tv": 70001},
        "season": {"tvdb": 1, "tmdb": 1},
    },
    # kitsu<->mal correspondence for the kitsu-keyed-source fixtures below,
    # deliberately carrying no cinemeta ids of their own
    {"mal_id": 900, "kitsu_id": 700},
    {"mal_id": 901, "kitsu_id": 701},
    {"mal_id": 902, "kitsu_id": 702},
    {"mal_id": 903, "kitsu_id": 703},
    {"mal_id": 904, "kitsu_id": 704},
    {"mal_id": 905, "kitsu_id": 705},
]
_MAL_SOURCE_JSON = json.dumps(_MAL_SOURCE_DATA)

_KITSU_SOURCE_DATA = [
    {"kitsu_id": 700, "imdb_id": "tt7000001", "title": "Single Cour Show"},
    {
        "kitsu_id": 701,
        "imdb_id": "tt7000002",
        "title": "Multi Cour Show S1",
        "fromSeason": 1,
        "fromEpisode": 1,
    },
    {
        "kitsu_id": 702,
        "imdb_id": "tt7000002",
        "title": "Multi Cour Show S2",
        "fromSeason": 2,
        "fromEpisode": 1,
    },
    {
        "kitsu_id": 703,
        "imdb_id": "tt7000003",
        "title": "Filler Show",
        "nonImdbEpisodes": [5],
    },
    {"kitsu_id": 704, "tvdb_id": "80001", "title": "TVDB Only Show"},
    {"kitsu_id": 705, "tvdbId": "80002", "title": "Inconsistent TVDB Key"},
]
_KITSU_SOURCE_JSON = json.dumps(_KITSU_SOURCE_DATA)


def _patch_files(mal_source=_MAL_SOURCE_JSON, kitsu_source=_KITSU_SOURCE_JSON):
    handles = [
        mock_open(read_data=mal_source).return_value,
        mock_open(read_data=kitsu_source).return_value,
    ]
    return patch("builtins.open", side_effect=handles)


def setup_function():
    mapping_module._mal_to_kitsu = {}
    mapping_module._kitsu_to_mal = {}
    mapping_module._mal_forward = {}
    mapping_module._mal_reverse = {t: {} for t in mapping_module.PRIORITY}
    mapping_module._kitsu_forward = {}
    mapping_module._kitsu_reverse = {t: {} for t in mapping_module.PRIORITY}
    mapping_module._loaded = False


# ----- Kitsu/MAL id round trip -----


def test_get_kitsu_id_from_mal_id_found():
    with _patch_files():
        load_mapping_db()
    exists, kitsu_id = get_kitsu_id_from_mal_id("123")
    assert exists is True
    assert kitsu_id == "14"


def test_get_kitsu_id_from_mal_id_not_found():
    with _patch_files():
        load_mapping_db()
    exists, kitsu_id = get_kitsu_id_from_mal_id("999")
    assert exists is False
    assert kitsu_id == ""


def test_get_kitsu_id_from_mal_id_strips_prefix():
    with _patch_files():
        load_mapping_db()
    exists, kitsu_id = get_kitsu_id_from_mal_id("mal:290")
    assert exists is True
    assert kitsu_id == "265"


def test_get_mal_id_from_kitsu_id_found():
    with _patch_files():
        load_mapping_db()
    exists, mal_id = get_mal_id_from_kitsu_id("14")
    assert exists is True
    assert mal_id == "123"


def test_get_mal_id_from_kitsu_id_not_found():
    with _patch_files():
        load_mapping_db()
    exists, mal_id = get_mal_id_from_kitsu_id("9999")
    assert exists is False
    assert mal_id == ""


def test_file_read_only_once():
    with _patch_files() as mock_file:
        load_mapping_db()
        load_mapping_db()
    assert mock_file.call_count == 2  # one read per mapping source file


def test_file_read_failure_returns_not_found():
    with patch("builtins.open", side_effect=OSError("not found")):
        load_mapping_db()
    exists, kitsu_id = get_kitsu_id_from_mal_id("123")
    assert exists is False
    assert kitsu_id == ""


def test_kitsu_source_failure_does_not_discard_mal_source():
    """A missing/corrupt imdb_mapping.json must not break plain mal:/kitsu:
    id resolution, which only depends on the independently-loaded MAL-keyed
    source."""
    handles = [
        mock_open(read_data=_MAL_SOURCE_JSON).return_value,
        FileNotFoundError("no such file"),
    ]
    with patch("builtins.open", side_effect=handles):
        load_mapping_db()
    exists, kitsu_id = get_kitsu_id_from_mal_id("123")
    assert exists is True
    assert kitsu_id == "14"


# ----- parse/format cinemeta ids -----


def test_parse_cinemeta_id_imdb_bare():
    assert parse_cinemeta_id("tt0123456") == ("imdb", "tt0123456", None, None)


def test_parse_cinemeta_id_imdb_with_season_episode():
    assert parse_cinemeta_id("tt0123456:1:5") == ("imdb", "tt0123456", 1, 5)


def test_parse_cinemeta_id_tvdb():
    assert parse_cinemeta_id("tvdb:12345:2:3") == ("tvdb", "12345", 2, 3)


def test_parse_cinemeta_id_tmdb():
    assert parse_cinemeta_id("tmdb:54321") == ("tmdb", "54321", None, None)


def test_parse_cinemeta_id_invalid():
    assert parse_cinemeta_id("mal:123") is None
    assert parse_cinemeta_id("kitsu:123") is None


def test_format_cinemeta_id_imdb():
    assert format_cinemeta_id("imdb", "tt0123456") == "tt0123456"


def test_format_cinemeta_id_tvdb():
    assert format_cinemeta_id("tvdb", "12345") == "tvdb:12345"


# ----- Priority chain resolution (outbound) -----


def test_resolve_outbound_prefers_kitsu_keyed_source():
    with _patch_files():
        load_mapping_db()
    mapping = resolve_outbound(kitsu_id=700)
    assert mapping.source == "imdb"
    assert mapping.identifier == "tt7000001"


def test_resolve_outbound_falls_back_to_mal_keyed_source():
    with _patch_files():
        load_mapping_db()
    mapping = resolve_outbound(mal_id=500)
    assert mapping.source == "imdb"
    assert mapping.identifier == "tt5000001"


def test_resolve_outbound_priority_order_imdb_over_tvdb_over_tmdb():
    with _patch_files():
        load_mapping_db()
    mapping = resolve_outbound(kitsu_id=704)
    assert mapping.source == "tvdb"
    assert mapping.identifier == "80001"


def test_resolve_outbound_tolerates_inconsistent_tvdb_key():
    with _patch_files():
        load_mapping_db()
    mapping = resolve_outbound(kitsu_id=705)
    assert mapping.source == "tvdb"
    assert mapping.identifier == "80002"


def test_resolve_outbound_falls_back_to_bare_kitsu_id():
    with _patch_files():
        load_mapping_db()
    mapping = resolve_outbound(mal_id=123)  # kitsu_id 14 has no cinemeta mapping
    assert mapping.source == "kitsu"
    assert mapping.identifier == "14"


def test_resolve_outbound_falls_back_to_mal_id():
    with _patch_files():
        load_mapping_db()
    mapping = resolve_outbound(mal_id=999999)
    assert mapping.source == "mal"
    assert mapping.identifier == "999999"


def test_resolve_outbound_requires_an_id():
    with _patch_files():
        load_mapping_db()
    with pytest.raises(ValueError):
        resolve_outbound()


# ----- Multi-season disambiguation + inbound resolution -----


def test_resolve_inbound_picks_first_cour_by_default():
    with _patch_files():
        load_mapping_db()
    resolution = resolve_inbound(
        identifier_type="imdb", identifier="tt7000002", season=1, episode=1
    )
    assert resolution is not None
    assert resolution.mal_id == "901"


def test_resolve_inbound_picks_second_cour_when_season_matches():
    with _patch_files():
        load_mapping_db()
    resolution = resolve_inbound(
        identifier_type="imdb", identifier="tt7000002", season=2, episode=1
    )
    assert resolution is not None
    assert resolution.mal_id == "902"
    assert resolution.flat_absolute_episode == 1


def test_resolve_inbound_computes_flat_absolute_episode():
    with _patch_files():
        load_mapping_db()
    resolution = resolve_inbound(
        identifier_type="imdb", identifier="tt7000001", season=1, episode=5
    )
    assert resolution is not None
    assert resolution.mal_id == "900"
    assert resolution.flat_absolute_episode == 5


def test_resolve_inbound_not_found():
    with _patch_files():
        load_mapping_db()
    resolution = resolve_inbound(
        identifier_type="imdb", identifier="tt0000000", season=1, episode=1
    )
    assert resolution is None


def test_resolve_inbound_falls_back_to_mal_keyed_source():
    with _patch_files():
        load_mapping_db()
    resolution = resolve_inbound(
        identifier_type="imdb", identifier="tt5000001", season=1, episode=1
    )
    assert resolution is not None
    assert resolution.mal_id == "500"


def test_resolve_outbound_next_season_boundary_ignores_same_season_siblings():
    """A sibling sharing the current entry's own from_season (a mid-season
    episode-only split, as seen in real-world 'season 0' specials data) must
    not be treated as the next season boundary — doing so would zero out the
    current entry's own season range entirely."""
    with _patch_files(
        kitsu_source=json.dumps(
            [
                {
                    "kitsu_id": 710,
                    "imdb_id": "tt7100001",
                    "fromSeason": 0,
                    "fromEpisode": 56,
                },
                {
                    "kitsu_id": 711,
                    "imdb_id": "tt7100001",
                    "fromSeason": 0,
                    "fromEpisode": 57,
                },
                {
                    "kitsu_id": 712,
                    "imdb_id": "tt7100001",
                    "fromSeason": 1,
                    "fromEpisode": 1,
                },
            ]
        )
    ):
        load_mapping_db()
    mapping = resolve_outbound(kitsu_id=710)
    assert mapping.next_from_season == 1


def test_resolve_inbound_exposes_non_imdb_episodes():
    with _patch_files():
        load_mapping_db()
    resolution = resolve_inbound(
        identifier_type="imdb", identifier="tt7000003", season=1, episode=1
    )
    assert resolution is not None
    assert resolution.non_imdb_episodes == frozenset({5})
