"""Tests for cross-filesystem move handling.

True cross-FS testing requires a second mount which we can't rely on in
CI, so we exercise the cross-FS code path directly via the public-ish
_move_cross_filesystem method. The same-FS atomic path is exercised
implicitly by the existing test_file_ops.py move tests.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from my_dropper_app.app import (
    FileOperationWorker,
    OperationMode,
)


@pytest.fixture
def worker(qapp):
    return FileOperationWorker(operations=[], mode=OperationMode.MOVE)


# ---------------------------------------------------------------------------
# Cross-FS detector
# ---------------------------------------------------------------------------


def test_is_cross_filesystem_returns_false_for_same_dir(tmp_path: Path) -> None:
    src = tmp_path / "s.txt"
    src.write_text("hi")
    dest = tmp_path / "out" / "s.txt"
    dest.parent.mkdir()

    assert FileOperationWorker._is_cross_filesystem(src, dest) is False


def test_is_cross_filesystem_handles_missing_source(tmp_path: Path) -> None:
    # Defensive: if we can't stat the source, the helper returns True so
    # the richer cross-FS error handling kicks in.
    src = tmp_path / "ghost.txt"
    dest = tmp_path / "dest.txt"
    assert FileOperationWorker._is_cross_filesystem(src, dest) is True


# ---------------------------------------------------------------------------
# Cross-FS file move
# ---------------------------------------------------------------------------


def test_cross_fs_file_move_copies_then_deletes(tmp_path: Path, worker) -> None:
    src = tmp_path / "doc.txt"
    src.write_text("payload")
    dest = tmp_path / "dest" / "doc.txt"
    dest.parent.mkdir()

    worker._move_cross_filesystem(src, dest)

    assert dest.read_text() == "payload"
    assert not src.exists(), "source must be removed after successful cross-FS move"


def test_cross_fs_file_move_preserves_metadata(tmp_path: Path, worker) -> None:
    import os
    import time

    src = tmp_path / "old.txt"
    src.write_text("aged")
    past = time.time() - 7 * 24 * 3600
    os.utime(src, (past, past))

    dest = tmp_path / "out" / "old.txt"
    dest.parent.mkdir()

    worker._move_cross_filesystem(src, dest)

    assert abs(dest.stat().st_mtime - past) < 2.0


# ---------------------------------------------------------------------------
# Cross-FS directory move
# ---------------------------------------------------------------------------


def test_cross_fs_directory_move(tmp_path: Path, worker) -> None:
    src = tmp_path / "tree"
    (src / "sub").mkdir(parents=True)
    (src / "a.txt").write_text("a")
    (src / "sub" / "b.txt").write_text("b")

    dest = tmp_path / "moved_tree"

    worker._move_cross_filesystem(src, dest)

    assert (dest / "a.txt").read_text() == "a"
    assert (dest / "sub" / "b.txt").read_text() == "b"
    assert not src.exists()


# ---------------------------------------------------------------------------
# Failure paths — phase-labelled RuntimeError messages
# ---------------------------------------------------------------------------


def test_copy_failure_preserves_source_and_reports_phase(
    tmp_path: Path, worker, monkeypatch
) -> None:
    src = tmp_path / "doc.txt"
    src.write_text("important")
    dest = tmp_path / "dest" / "doc.txt"
    dest.parent.mkdir()

    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(shutil, "copy2", boom)

    with pytest.raises(RuntimeError, match="cross-filesystem copy failed.*source preserved"):
        worker._move_cross_filesystem(src, dest)

    assert src.exists(), "source must remain after a copy failure"
    assert src.read_text() == "important"
    assert not dest.exists(), "any partial destination must be cleaned up"


def test_delete_failure_after_copy_warns_about_both_locations(
    tmp_path: Path, worker, monkeypatch
) -> None:
    src = tmp_path / "doc.txt"
    src.write_text("payload")
    dest = tmp_path / "dest" / "doc.txt"
    dest.parent.mkdir()

    real_unlink = Path.unlink

    def fail_unlink(self, missing_ok=False):
        # Only the source-delete call should fail; let other unlinks proceed.
        if self == src:
            raise PermissionError("simulated permission denied")
        return real_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", fail_unlink)

    with pytest.raises(RuntimeError, match="BOTH locations"):
        worker._move_cross_filesystem(src, dest)

    # The copy itself completed, so destination must exist…
    assert dest.exists()
    assert dest.read_text() == "payload"
    # …and the source is still there (that's the whole point of the warning).
    assert src.exists()


def test_size_mismatch_after_copy_drops_corrupt_destination(
    tmp_path: Path, worker, monkeypatch
) -> None:
    src = tmp_path / "doc.txt"
    src.write_text("the original")
    dest = tmp_path / "dest" / "doc.txt"
    dest.parent.mkdir()

    def fake_copy(s, d):
        # Simulate a corrupt copy that's the wrong size
        Path(d).write_text("short")

    monkeypatch.setattr(shutil, "copy2", fake_copy)

    with pytest.raises(RuntimeError, match="size mismatch"):
        worker._move_cross_filesystem(src, dest)

    assert src.exists(), "source must be preserved when verification fails"
    assert not dest.exists(), "corrupt destination must be removed"
