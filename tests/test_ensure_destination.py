"""Tests for FileDropperApp._ensure_destination_exists.

These bypass full widget construction by calling the method as an
unbound function with a minimal stand-in `self`. The helper only
touches `self.destination_directory` and `self._log` on the success
paths; the dialog branch is exercised once via monkeypatching.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from my_dropper_app.app import FileDropperApp


def _make_self(default_dest: Path):
    """Build a minimal stand-in `self` that captures log lines."""
    logs: list[str] = []
    fake = SimpleNamespace(
        destination_directory=default_dest,
        _log=logs.append,
    )
    return fake, logs


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def test_existing_directory_returns_true_without_logging(tmp_path: Path) -> None:
    fake, logs = _make_self(tmp_path)
    assert FileDropperApp._ensure_destination_exists(fake) is True
    # No "Created directory" line should be emitted when nothing was created
    assert all("Created directory" not in line for line in logs)


def test_creates_missing_directory_and_logs(tmp_path: Path) -> None:
    target = tmp_path / "deep" / "nested" / "dest"
    fake, logs = _make_self(target)

    result = FileDropperApp._ensure_destination_exists(fake)

    assert result is True
    assert target.is_dir()
    assert any("Created directory" in line and str(target) in line for line in logs)


def test_explicit_path_overrides_default(tmp_path: Path) -> None:
    default_dest = tmp_path / "default"
    explicit = tmp_path / "explicit"

    fake, _logs = _make_self(default_dest)
    result = FileDropperApp._ensure_destination_exists(fake, explicit)

    assert result is True
    assert explicit.is_dir()
    assert not default_dest.exists(), "the default path should not be touched"


# ---------------------------------------------------------------------------
# Failure path
# ---------------------------------------------------------------------------


def test_mkdir_failure_returns_false_and_logs(
    tmp_path: Path, monkeypatch
) -> None:
    target = tmp_path / "doomed"
    fake, logs = _make_self(target)

    def boom(self, *_args, **_kwargs):
        raise PermissionError("simulated permission denied")

    monkeypatch.setattr(Path, "mkdir", boom)

    result = FileDropperApp._ensure_destination_exists(fake)

    assert result is False
    assert any("Cannot create destination" in line for line in logs)
    assert not target.exists()


def test_show_error_dialog_invokes_critical(
    tmp_path: Path, monkeypatch
) -> None:
    """When show_error_dialog=True and mkdir fails, QMessageBox.critical fires."""
    target = tmp_path / "doomed"
    fake, _logs = _make_self(target)

    def boom(self, *_args, **_kwargs):
        raise OSError("disk gone")

    monkeypatch.setattr(Path, "mkdir", boom)

    dialog_calls: list[tuple] = []

    def fake_critical(*args, **_kwargs):
        dialog_calls.append(args)

    from my_dropper_app import app as app_module
    monkeypatch.setattr(app_module.QMessageBox, "critical", fake_critical)

    result = FileDropperApp._ensure_destination_exists(
        fake, show_error_dialog=True
    )

    assert result is False
    assert len(dialog_calls) == 1, "critical dialog should be shown exactly once"
