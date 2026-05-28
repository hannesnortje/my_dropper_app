"""Tests for parse_text_for_filename (the pure helper in parsing.py)."""
from __future__ import annotations

from my_dropper_app.parsing import parse_text_for_filename


def _parse(text: str) -> tuple[str, str]:
    return parse_text_for_filename(text)


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
    base, ext = _parse('{"ior": {"notModelId": "x"}}')
    assert base == "dropped_text"
    assert ext == "json"


def test_modelid_with_non_string_type_falls_through_to_generic_json() -> None:
    # int instead of str — previously triggered AttributeError caught by
    # the generic except Exception (returns defaults but logs a confusing
    # "Error parsing text" line). Now the isinstance(str) guard makes this
    # the same clean fall-through as a missing key.
    base, ext = _parse('{"ior": {"modelId": 123}}')
    assert base == "dropped_text"
    assert ext == "json"


def test_modelid_with_list_type_falls_through_to_generic_json() -> None:
    base, ext = _parse('{"ior": {"modelId": ["a", "b"]}}')
    assert base == "dropped_text"
    assert ext == "json"


def test_publicdata_name_with_non_string_type_falls_through() -> None:
    base, ext = _parse('{"publicData": {"name": 42}}')
    assert base == "dropped_text"
    assert ext == "json"


def test_ior_value_is_not_a_dict_falls_through() -> None:
    # ior present but not a dict (e.g. a bare string)
    base, ext = _parse('{"ior": "just a string"}')
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
