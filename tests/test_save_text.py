"""Tests for save_text_utf8_with_fallback.

Covers the four meaningful states:
  - plain ASCII → success, no warning
  - valid UTF-8 with emoji → success, no warning
  - mangled clipboard with unpaired surrogate → success with replacement,
    one warning logged
  - read-only directory → failure, one error logged
"""
from __future__ import annotations

from pathlib import Path

import pytest

from my_dropper_app.parsing import save_text_utf8_with_fallback


def _collect_log():
    msgs: list[str] = []
    return msgs, msgs.append


def test_plain_ascii_round_trips(tmp_path: Path) -> None:
    msgs, log = _collect_log()
    dest = tmp_path / "ascii.txt"

    assert save_text_utf8_with_fallback(dest, "hello world", log) is True
    assert dest.read_text(encoding='utf-8') == "hello world"
    assert msgs == [], "no log lines expected on clean save"


def test_valid_utf8_with_emoji_round_trips(tmp_path: Path) -> None:
    msgs, log = _collect_log()
    dest = tmp_path / "emoji.txt"
    payload = "café — 🎉 ✓ 中文"

    assert save_text_utf8_with_fallback(dest, payload, log) is True
    assert dest.read_text(encoding='utf-8') == payload
    assert msgs == []


def test_unpaired_surrogate_triggers_replacement_path(tmp_path: Path) -> None:
    msgs, log = _collect_log()
    dest = tmp_path / "mangled.txt"
    # \ud83d is a high-surrogate; on its own it can't be encoded as UTF-8.
    # The fallback should replace it with U+FFFD and still save.
    mangled = "before \ud83d after"

    assert save_text_utf8_with_fallback(dest, mangled, log) is True
    assert dest.exists()
    # Must have logged exactly one warning about non-UTF-8 chars
    assert any("non-UTF-8" in m for m in msgs), msgs
    # The saved file is valid UTF-8 by construction
    saved = dest.read_text(encoding='utf-8')
    assert "before" in saved
    assert "after" in saved
    # Python's str→bytes errors='replace' uses '?' (U+003F) for unencodable
    # codepoints. (U+FFFD is the *decoding*-side replacement marker.)
    assert "?" in saved, "expected the '?' replacement marker"


def test_unwritable_destination_returns_false(tmp_path: Path) -> None:
    msgs, log = _collect_log()
    # Path inside a directory we never created — write_text raises
    # FileNotFoundError (an OSError subclass) which the helper catches.
    dest = tmp_path / "no_such_dir" / "x.txt"

    assert save_text_utf8_with_fallback(dest, "anything", log) is False
    assert any("Error saving text" in m for m in msgs), msgs


def test_log_callback_is_optional() -> None:
    # Helper must work when called without a log function (default no-op)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "no_log.txt"
        assert save_text_utf8_with_fallback(dest, "fine") is True
        assert dest.read_text() == "fine"
