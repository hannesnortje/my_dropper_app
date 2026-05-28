"""Shared pytest fixtures for the my_dropper_app test suite."""
from __future__ import annotations

import pytest

# pytest-qt provides the `qtbot` and `qapp` fixtures automatically.
# We just ensure QSettings writes to an isolated location during tests so we
# never pollute the user's real configuration.


@pytest.fixture(autouse=True)
def isolated_qsettings(tmp_path, monkeypatch):
    """Redirect QSettings to a temp directory for every test.

    Without this, tests that instantiate FileDropperApp would read and write
    against ~/.config/CeruleanCircle/, which is the user's real settings.
    """
    from PyQt6.QtCore import QSettings

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        str(tmp_path / "qsettings"),
    )
    yield
