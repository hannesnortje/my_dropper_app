"""Defensive-load tests for FileDropperApp._init_settings.

These exercise the method as an unbound function with a tiny fake
QSettings, so they don't construct a real widget. The fake lets us
inject corrupted values and even outright exceptions on .value() to
prove the load never crashes the app.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from my_dropper_app.app import FileDropperApp
from my_dropper_app.constants import (
    DEFAULT_DEST_DIR,
    SETTINGS_DEST_DIR,
    SETTINGS_OPERATION_MODE,
    SETTINGS_RECENT_DESTINATIONS,
)
from my_dropper_app.models import OperationMode


class FakeSettings:
    """Minimal QSettings stand-in.

    Stores values, returns defaults for unknown keys, and supports a
    `raise_on` set of keys that triggers a ValueError when read — used
    to simulate a corrupted config file.
    """

    _RAISE = object()

    def __init__(self, values=None, raise_on=None):
        self._values = dict(values or {})
        self._raise_on = set(raise_on or ())
        self.writes: dict[str, object] = {}

    def value(self, key, default=None, **_kwargs):
        if key in self._raise_on:
            raise ValueError(f"corrupted setting: {key}")
        return self._values.get(key, default)

    def setValue(self, key, value):
        self.writes[key] = value
        self._values[key] = value


def _fresh_self(settings):
    """Build a minimal stand-in widget."""
    return SimpleNamespace(settings=settings)


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def test_empty_settings_uses_defaults() -> None:
    fake = _fresh_self(FakeSettings())

    FileDropperApp._init_settings(fake)

    assert fake.destination_directory == DEFAULT_DEST_DIR
    assert fake.operation_mode == OperationMode.COPY
    assert fake.recent_destinations == []


def test_valid_settings_are_loaded(tmp_path: Path) -> None:
    settings = FakeSettings({
        SETTINGS_DEST_DIR: str(tmp_path),
        SETTINGS_OPERATION_MODE: "move",
    })
    fake = _fresh_self(settings)

    FileDropperApp._init_settings(fake)

    assert fake.destination_directory == tmp_path
    assert fake.operation_mode == OperationMode.MOVE


def test_recents_with_existing_directories_are_kept(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    settings = FakeSettings({
        SETTINGS_RECENT_DESTINATIONS: [str(a), str(b)],
    })
    fake = _fresh_self(settings)

    FileDropperApp._init_settings(fake)

    assert fake.recent_destinations == [str(a), str(b)]


# ---------------------------------------------------------------------------
# Defensive paths
# ---------------------------------------------------------------------------


def test_value_raising_does_not_crash() -> None:
    """If QSettings.value itself raises (corrupt .conf file), defaults
    must already be in place and the load must complete cleanly."""
    settings = FakeSettings(raise_on={SETTINGS_DEST_DIR})
    fake = _fresh_self(settings)

    FileDropperApp._init_settings(fake)

    assert fake.destination_directory == DEFAULT_DEST_DIR
    assert fake.operation_mode == OperationMode.COPY
    assert fake.recent_destinations == []


def test_recents_returned_as_single_string_is_normalised(tmp_path: Path) -> None:
    """Qt's QSettings returns a bare str when a list has only one entry.
    The defensive load must wrap it back into a list before pruning."""
    only = tmp_path / "only"
    only.mkdir()
    settings = FakeSettings({SETTINGS_RECENT_DESTINATIONS: str(only)})
    fake = _fresh_self(settings)

    FileDropperApp._init_settings(fake)

    assert fake.recent_destinations == [str(only)]


def test_recents_with_non_string_elements_are_filtered() -> None:
    """Hand-edited config might contain mixed types in the list. We drop
    non-strings rather than letting Path() blow up downstream."""
    settings = FakeSettings({SETTINGS_RECENT_DESTINATIONS: ["a string", 42, None, "/tmp"]})
    fake = _fresh_self(settings)

    FileDropperApp._init_settings(fake)

    # The two strings survive the type filter; prune drops the non-existent
    # "a string" entry. /tmp exists on POSIX so it's kept.
    assert all(isinstance(r, str) for r in fake.recent_destinations)
    # Numbers and None must not appear
    assert 42 not in fake.recent_destinations
    assert None not in fake.recent_destinations


def test_wrong_type_dest_dir_falls_back_to_default() -> None:
    """If DEST_DIR somehow holds a non-string-convertible value (would be
    extraordinary in practice, but hand-edited configs are wild), Path()
    on the unconvertible value raises — caught and ignored."""
    class Hostile:
        def __str__(self):
            raise TypeError("won't render")

    settings = FakeSettings({SETTINGS_DEST_DIR: Hostile()})
    fake = _fresh_self(settings)

    FileDropperApp._init_settings(fake)

    assert fake.destination_directory == DEFAULT_DEST_DIR


def test_partial_failure_preserves_earlier_loads(tmp_path: Path) -> None:
    """If DEST_DIR loads fine but RECENTS reading raises, we keep the
    DEST_DIR we already loaded — not reset everything to default."""
    settings = FakeSettings(
        values={SETTINGS_DEST_DIR: str(tmp_path)},
        raise_on={SETTINGS_RECENT_DESTINATIONS},
    )
    fake = _fresh_self(settings)

    FileDropperApp._init_settings(fake)

    # destination_directory was loaded BEFORE the recents read; that's preserved
    assert fake.destination_directory == tmp_path
    # recents stayed at its initial default
    assert fake.recent_destinations == []
