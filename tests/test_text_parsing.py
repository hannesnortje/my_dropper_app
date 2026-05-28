"""Tests for FileDropperApp._parse_text_for_filename.

These tests bypass full widget construction by calling the method as an
unbound function with a minimal `self` that only exposes `_log`. The
parser writes log lines but otherwise reads nothing from `self`.
"""
from __future__ import annotations

from types import SimpleNamespace

from my_dropper_app.app import FileDropperApp


def _parse(text: str) -> tuple[str, str]:
    fake_self = SimpleNamespace(_log=lambda _msg: None)
    return FileDropperApp._parse_text_for_filename(fake_self, text)


def test_ior_model_id_produces_scenario_filename() -> None:
    base, ext = _parse('{"ior": {"modelId": "abc-123"}}')
    assert base == "abc-123.scenario"
    assert ext == "json"


def test_public_data_name_produces_ior_filename() -> None:
    base, ext = _parse('{"publicData": {"name": "My Scenario"}}')
    assert base == "My Scenario"
    assert ext == "ior"


def test_public_data_name_strips_unsafe_characters() -> None:
    base, ext = _parse('{"publicData": {"name": "weird/name<with>bad?chars"}}')
    # only alnum, space, hyphen, underscore, dot survive
    assert "/" not in base
    assert "<" not in base
    assert ">" not in base
    assert "?" not in base
    assert ext == "ior"


def test_generic_json_falls_back_to_json_extension() -> None:
    base, ext = _parse('{"unrelated": "value"}')
    assert base == "dropped_text"
    assert ext == "json"


def test_malformed_json_returns_plain_text_defaults() -> None:
    base, ext = _parse("not really {json}")
    assert base == "dropped_text"
    assert ext == "txt"


def test_empty_string_returns_defaults() -> None:
    base, ext = _parse("")
    assert base == "dropped_text"
    assert ext == "txt"


def test_ior_present_but_modelid_missing_falls_through_to_generic_json() -> None:
    # NOTE: this exercises the M5 issue noted in IMPROVEMENT_PLAN — currently
    # the code handles missing modelId gracefully via .get(), but an
    # intermediate type mismatch (e.g. ior.modelId is an int) is not yet
    # type-checked. We assert the current safe behavior.
    base, ext = _parse('{"ior": {"notModelId": "x"}}')
    assert base == "dropped_text"
    assert ext == "json"


def test_public_data_present_but_name_missing_falls_through() -> None:
    base, ext = _parse('{"publicData": {"description": "no name here"}}')
    assert base == "dropped_text"
    assert ext == "json"


def test_modelid_whitespace_only_is_ignored() -> None:
    base, ext = _parse('{"ior": {"modelId": "   "}}')
    assert base == "dropped_text"
    assert ext == "json"


def test_top_level_array_is_treated_as_generic_json() -> None:
    # json.loads succeeds but isinstance(data, dict) is False
    base, ext = _parse("[1, 2, 3]")
    # falls through all dict checks; ext is never assigned to "json" because
    # that assignment is inside the `isinstance(data, dict)` branch
    assert base == "dropped_text"
    assert ext == "txt"
