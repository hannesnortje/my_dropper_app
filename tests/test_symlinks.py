"""Tests for the symlink-skip policy.

Top-level symlinks must never be silently followed: that would copy
(or worse, move and delete) the symlink's target rather than the
symlink itself, and a circular symlink would crash the worker.
Inside a copied/moved tree, nested symlinks are preserved as symlinks
so circular structures stay finite.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from my_dropper_app.models import (
    FileOperation,
    OperationMode,
    OperationStatus,
)
from my_dropper_app.worker import FileOperationWorker


pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="symlink creation on Windows requires elevated privileges",
)


@pytest.fixture
def worker_copy(qapp):
    return FileOperationWorker(operations=[], mode=OperationMode.COPY)


# ---------------------------------------------------------------------------
# Top-level symlinks are skipped, not followed
# ---------------------------------------------------------------------------


def test_top_level_symlink_to_file_is_skipped(tmp_path: Path, worker_copy) -> None:
    real = tmp_path / "real.txt"
    real.write_text("important")
    link = tmp_path / "link.txt"
    link.symlink_to(real)

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    worker_copy.operations = [
        FileOperation(
            source=link,
            destination=dest_dir / link.name,
            mode=OperationMode.COPY,
            status=OperationStatus.PENDING,
        )
    ]
    results = []
    worker_copy.operation_completed.connect(lambda r: results.append(r))
    worker_copy.run()

    assert len(results) == 1
    assert results[0].skipped_count == 1
    assert results[0].success_count == 0
    # Nothing was copied
    assert not (dest_dir / link.name).exists()
    # Source link and its target are untouched
    assert link.is_symlink()
    assert real.exists()


def test_top_level_symlink_to_directory_is_skipped(
    tmp_path: Path, worker_copy
) -> None:
    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    (real_dir / "inside.txt").write_text("inside")

    link = tmp_path / "link_dir"
    link.symlink_to(real_dir, target_is_directory=True)

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    worker_copy.operations = [
        FileOperation(
            source=link,
            destination=dest_dir / link.name,
            mode=OperationMode.COPY,
            status=OperationStatus.PENDING,
        )
    ]
    results = []
    worker_copy.operation_completed.connect(lambda r: results.append(r))
    worker_copy.run()

    assert results[0].skipped_count == 1
    assert results[0].success_count == 0


def test_top_level_broken_symlink_is_skipped(tmp_path: Path, worker_copy) -> None:
    # Symlink pointing at a path that never existed
    link = tmp_path / "dangling"
    link.symlink_to(tmp_path / "nope_no_such_target")

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    worker_copy.operations = [
        FileOperation(
            source=link,
            destination=dest_dir / link.name,
            mode=OperationMode.COPY,
            status=OperationStatus.PENDING,
        )
    ]
    results = []
    worker_copy.operation_completed.connect(lambda r: results.append(r))
    worker_copy.run()

    # Specifically the symlink branch (not the "unsupported item" branch)
    # should catch this — both are skipped but the symlink one is the
    # accurate one for a broken link.
    assert results[0].skipped_count == 1
    assert results[0].success_count == 0


# ---------------------------------------------------------------------------
# Symlinks INSIDE a copied tree are preserved, not followed
# ---------------------------------------------------------------------------


def test_directory_with_inner_symlink_preserves_link(
    tmp_path: Path, worker_copy
) -> None:
    src = tmp_path / "tree"
    src.mkdir()
    (src / "real.txt").write_text("real content")
    (src / "alias.txt").symlink_to(src / "real.txt")

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    worker_copy.operations = [
        FileOperation(
            source=src,
            destination=dest_dir / src.name,
            mode=OperationMode.COPY,
            status=OperationStatus.PENDING,
        )
    ]
    results = []
    worker_copy.operation_completed.connect(lambda r: results.append(r))
    worker_copy.run()

    copied_tree = dest_dir / "tree"
    assert results[0].success_count == 1
    assert (copied_tree / "real.txt").read_text() == "real content"
    # The crucial property: alias.txt remains a symlink rather than a
    # duplicated regular file. (Without symlinks=True on copytree, it
    # would have been silently materialised.)
    assert (copied_tree / "alias.txt").is_symlink()


def test_directory_with_circular_symlink_does_not_recurse(
    tmp_path: Path, worker_copy
) -> None:
    # tree/loop -> tree/  (a symlink pointing back at its own parent)
    src = tmp_path / "tree"
    src.mkdir()
    (src / "real.txt").write_text("x")
    (src / "loop").symlink_to(src, target_is_directory=True)

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    worker_copy.operations = [
        FileOperation(
            source=src,
            destination=dest_dir / src.name,
            mode=OperationMode.COPY,
            status=OperationStatus.PENDING,
        )
    ]
    results = []
    worker_copy.operation_completed.connect(lambda r: results.append(r))
    worker_copy.run()

    # The key assertion: the run completed (no infinite recursion, no
    # stack overflow). With symlinks=True the loop symlink is preserved
    # rather than walked.
    assert results[0].success_count == 1
    assert (dest_dir / "tree" / "real.txt").read_text() == "x"
    assert (dest_dir / "tree" / "loop").is_symlink()
