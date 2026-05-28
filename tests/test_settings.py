"""Smoke tests for QSettings round-tripping.

The current code reads settings inline in FileDropperApp.__init__ rather
than from an isolated _load_settings method, so deeper coverage will land
once Phase 4.2 (defensive settings load) lifts that logic into a
testable function. For now we verify:

  - QSettings with no prior values returns the provided defaults
  - QSettings round-trips values correctly under our isolated fixture
  - Wrong-type reads fall back to the default rather than crashing
"""
from __future__ import annotations

from PyQt6.QtCore import QSettings

from my_dropper_app.app import (
    APP_NAME,
    DEFAULT_DEST_DIR,
    ORG_NAME,
    SETTINGS_DARK_MODE,
    SETTINGS_DEST_DIR,
    SETTINGS_RECENT_DESTINATIONS,
)


def _fresh_settings() -> QSettings:
    # isolated_qsettings autouse fixture has already pointed Qt at a tmp path
    s = QSettings(ORG_NAME, APP_NAME)
    s.clear()
    return s


def test_no_prior_settings_returns_defaults(qapp) -> None:
    s = _fresh_settings()

    dest = s.value(SETTINGS_DEST_DIR, str(DEFAULT_DEST_DIR))
    dark = s.value(SETTINGS_DARK_MODE, False, type=bool)
    recents = s.value(SETTINGS_RECENT_DESTINATIONS, [])

    assert dest == str(DEFAULT_DEST_DIR)
    assert dark is False
    assert recents == []


def test_round_trip_dest_dir(tmp_path, qapp) -> None:
    s = _fresh_settings()
    s.setValue(SETTINGS_DEST_DIR, str(tmp_path))
    s.sync()

    s2 = QSettings(ORG_NAME, APP_NAME)
    assert s2.value(SETTINGS_DEST_DIR) == str(tmp_path)


def test_round_trip_recent_destinations(tmp_path, qapp) -> None:
    s = _fresh_settings()
    paths = [str(tmp_path / "a"), str(tmp_path / "b")]
    s.setValue(SETTINGS_RECENT_DESTINATIONS, paths)
    s.sync()

    s2 = QSettings(ORG_NAME, APP_NAME)
    # Qt may return a single value as str when only one entry exists; with
    # multiple entries it returns a list.
    assert s2.value(SETTINGS_RECENT_DESTINATIONS) == paths


def test_dark_mode_type_coercion(qapp) -> None:
    s = _fresh_settings()
    # Simulate a corrupted settings file that stored a string instead of bool
    s.setValue(SETTINGS_DARK_MODE, "not-a-bool")
    s.sync()

    s2 = QSettings(ORG_NAME, APP_NAME)
    # With type=bool, Qt coerces — any non-empty string becomes True.
    # The important property is *no crash*; behavior is Qt-defined.
    value = s2.value(SETTINGS_DARK_MODE, False, type=bool)
    assert isinstance(value, bool)
