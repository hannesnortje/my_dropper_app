"""Tests for FileDropperApp._open_destination per-platform error paths.

Each platform branch wraps its own native call in a try/except so the
log line names the actual failure. We exercise the three most common
failure modes via SimpleNamespace + monkeypatch, without instantiating
the full widget.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from my_dropper_app import app as app_module
from my_dropper_app.app import FileDropperApp


def _make_self(dest: Path):
    logs: list[str] = []
    fake = SimpleNamespace(
        destination_directory=dest,
        _log=logs.append,
        _ensure_destination_exists=lambda *a, **k: True,
    )
    return fake, logs


# ---------------------------------------------------------------------------
# Linux branch
# ---------------------------------------------------------------------------


def test_linux_missing_xdg_open_shows_install_hint(
    tmp_path: Path, monkeypatch
) -> None:
    fake, logs = _make_self(tmp_path)

    monkeypatch.setattr(app_module.platform, "system", lambda: "Linux")

    def missing(*_args, **_kwargs):
        raise FileNotFoundError("xdg-open")

    monkeypatch.setattr(app_module.subprocess, "run", missing)

    FileDropperApp._open_destination(fake)

    assert any("xdg-utils" in line for line in logs), logs
    assert all("Opened:" not in line for line in logs)


def test_linux_xdg_open_nonzero_exit_is_reported(
    tmp_path: Path, monkeypatch
) -> None:
    fake, logs = _make_self(tmp_path)

    monkeypatch.setattr(app_module.platform, "system", lambda: "Linux")

    def fail(cmd, check):
        raise subprocess.CalledProcessError(returncode=4, cmd=cmd)

    monkeypatch.setattr(app_module.subprocess, "run", fail)

    FileDropperApp._open_destination(fake)

    assert any("xdg-open" in line and "exit 4" in line for line in logs), logs


def test_linux_success_logs_opened(tmp_path: Path, monkeypatch) -> None:
    fake, logs = _make_self(tmp_path)

    monkeypatch.setattr(app_module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0),
    )

    FileDropperApp._open_destination(fake)

    assert any("📂 Opened:" in line for line in logs), logs


# ---------------------------------------------------------------------------
# Windows branch
# ---------------------------------------------------------------------------


def test_windows_startfile_failure_is_now_caught(
    tmp_path: Path, monkeypatch
) -> None:
    """Previously os.startfile() was entirely unguarded — an exception
    would propagate out of _open_destination and crash the click handler.
    Now OSError is caught and logged cleanly."""
    fake, logs = _make_self(tmp_path)

    monkeypatch.setattr(app_module.platform, "system", lambda: "Windows")

    def boom(_path):
        raise OSError("simulated startfile failure")

    # os.startfile only exists on Windows; inject it on the os module
    # for the duration of the test.
    monkeypatch.setattr(app_module.os, "startfile", boom, raising=False)

    FileDropperApp._open_destination(fake)

    assert any("Could not open in Explorer" in line for line in logs), logs
    assert any("startfile failure" in line for line in logs), logs


def test_windows_startfile_success_logs_opened(
    tmp_path: Path, monkeypatch
) -> None:
    fake, logs = _make_self(tmp_path)

    monkeypatch.setattr(app_module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(
        app_module.os, "startfile", lambda _p: None, raising=False
    )

    FileDropperApp._open_destination(fake)

    assert any("📂 Opened:" in line for line in logs), logs
