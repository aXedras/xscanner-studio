import json

import pytest

from xscanner.ai.infrastructure.prompt_helpers import (
    read_required_json_object,
    read_required_prompt_text,
)
from xscanner.mapping.whitelists import build_whitelist_hints, load_whitelist, whitelist_hint


def test_read_required_prompt_text_strips_and_returns(tmp_path):
    p = tmp_path / "prompt.md"
    p.write_text("\n  hello  \n", encoding="utf-8")

    assert read_required_prompt_text(p) == "hello"


def test_read_required_prompt_text_raises_on_empty(tmp_path):
    p = tmp_path / "prompt.md"
    p.write_text("   \n\n", encoding="utf-8")

    with pytest.raises(ValueError):
        read_required_prompt_text(p)


def test_read_required_json_object_returns_dict(tmp_path):
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps({"a": 1}), encoding="utf-8")

    assert read_required_json_object(p) == {"a": 1}


def test_read_required_json_object_raises_on_non_object(tmp_path):
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(ValueError):
        read_required_json_object(p)


def test_load_whitelist_parses_values_and_aliases(tmp_path):
    base = tmp_path / "whitelists"
    base.mkdir()

    (base / "metals.json").write_text(
        json.dumps({"values": ["Gold", "Silver"], "aliases": {"Au": "Gold"}}),
        encoding="utf-8",
    )

    wl = load_whitelist(file_name="metals.json", base_dir=base)
    assert wl.values == ["Gold", "Silver"]
    assert wl.aliases == {"Au": "Gold"}


def test_load_whitelist_is_defensive_on_bad_types(tmp_path):
    base = tmp_path / "whitelists"
    base.mkdir()

    (base / "bad.json").write_text(
        json.dumps({"values": "nope", "aliases": ["nope"]}),
        encoding="utf-8",
    )

    wl = load_whitelist(file_name="bad.json", base_dir=base)
    assert wl.values == []
    assert wl.aliases == {}


def test_build_whitelist_hints_uses_custom_keys(tmp_path):
    base = tmp_path / "whitelists"
    base.mkdir()

    (base / "producers.json").write_text(
        json.dumps({"values": ["Heraeus"], "aliases": {"AH": "Heraeus"}}),
        encoding="utf-8",
    )

    hints = build_whitelist_hints(
        [
            whitelist_hint(
                file_name="producers.json",
                values_key="ALLOWED_PRODUCERS",
                aliases_key="PRODUCER_ALIASES",
            )
        ],
        base_dir=base,
    )

    assert hints == {"ALLOWED_PRODUCERS": ["Heraeus"], "PRODUCER_ALIASES": {"AH": "Heraeus"}}
