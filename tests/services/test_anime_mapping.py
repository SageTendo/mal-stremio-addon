import json
from unittest.mock import mock_open, patch

import app.services.anime_mapping as mapping_module
from app.services.anime_mapping import (
    get_kitsu_id_from_mal_id,
    get_mal_id_from_kitsu_id,
    load_mapping_db,
)

_SAMPLE_DATA = [
    {"mal_id": 290, "kitsu_id": 265, "type": "TV"},
    {"mal_id": 123, "kitsu_id": 14, "type": "TV"},
    {"type": "OVA"},  # entry missing both ids
]
_SAMPLE_JSON = json.dumps(_SAMPLE_DATA)


def _patch_file(data=_SAMPLE_JSON):
    return patch("builtins.open", mock_open(read_data=data))


def setup_function():
    mapping_module._mal_to_kitsu = {}
    mapping_module._kitsu_to_mal = {}
    mapping_module._loaded = False


def test_get_kitsu_id_from_mal_id_found():
    with _patch_file():
        load_mapping_db()
    exists, kitsu_id = get_kitsu_id_from_mal_id("123")
    assert exists is True
    assert kitsu_id == "14"


def test_get_kitsu_id_from_mal_id_not_found():
    with _patch_file():
        load_mapping_db()
    exists, kitsu_id = get_kitsu_id_from_mal_id("999")
    assert exists is False
    assert kitsu_id == ""


def test_get_kitsu_id_from_mal_id_strips_prefix():
    with _patch_file():
        load_mapping_db()
    exists, kitsu_id = get_kitsu_id_from_mal_id("mal:290")
    assert exists is True
    assert kitsu_id == "265"


def test_get_mal_id_from_kitsu_id_found():
    with _patch_file():
        load_mapping_db()
    exists, mal_id = get_mal_id_from_kitsu_id("14")
    assert exists is True
    assert mal_id == "123"


def test_get_mal_id_from_kitsu_id_not_found():
    with _patch_file():
        load_mapping_db()
    exists, mal_id = get_mal_id_from_kitsu_id("9999")
    assert exists is False
    assert mal_id == ""


def test_file_read_only_once():
    with _patch_file() as mock_file:
        load_mapping_db()
        load_mapping_db()
    assert mock_file.call_count == 1


def test_file_read_failure_returns_not_found():
    with patch("builtins.open", side_effect=OSError("not found")):
        load_mapping_db()
    exists, kitsu_id = get_kitsu_id_from_mal_id("123")
    assert exists is False
    assert kitsu_id == ""
