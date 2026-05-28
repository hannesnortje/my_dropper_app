"""Tests for the destination-path validator."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from my_dropper_app.app import validate_destination


def test_existing_writable_directory_is_valid(tmp_path: Path) -> None:
    assert validate_destination(tmp_path) is None


def test_nonexistent_path_is_rejected(tmp_path: Path) -> None:
    assert validate_destination(tmp_path / "no-such-dir") == "does not exist"


def test_file_instead_of_directory_is_rejected(tmp_path: Path) -> None:
    f = tmp_path / "a-file.txt"
    f.write_text("nope")
    assert validate_destination(f) == "not a directory"


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="POSIX mode bits don't reliably revoke write access on Windows",
)
@pytest.mark.skipif(
    os.geteuid() == 0 if hasattr(os, "geteuid") else False,
    reason="root bypasses POSIX write-permission checks",
)
def test_readonly_directory_is_rejected(tmp_path: Path) -> None:
    readonly = tmp_path / "locked"
    readonly.mkdir()
    readonly.chmod(0o555)  # r-x r-x r-x — no write
    try:
        assert validate_destination(readonly) == "no write permission"
    finally:
        # Restore so pytest can clean up the tmp dir without errors
        readonly.chmod(0o755)
