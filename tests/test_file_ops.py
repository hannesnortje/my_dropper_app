"""End-to-end tests for the file-operation worker.

These tests instantiate a real FileOperationWorker and invoke its private
processing methods directly (without start()/QThread machinery) so we can
verify the on-disk results synchronously. Signal emissions are harmless
because pytest-qt provides a QApplication.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from my_dropper_app.models import (
    FileOperation,
    OperationMode,
    OperationResult,
    OperationStatus,
)
from my_dropper_app.worker import FileOperationWorker


@pytest.fixture
def worker_copy(qapp):
    return FileOperationWorker(operations=[], mode=OperationMode.COPY)


@pytest.fixture
def worker_move(qapp):
    return FileOperationWorker(operations=[], mode=OperationMode.MOVE)


def _make_op(src: Path, dest_dir: Path) -> FileOperation:
    return FileOperation(
        source=src,
        destination=dest_dir / src.name,
        mode=OperationMode.COPY,  # mode on the op is informational; worker uses self.mode
        status=OperationStatus.PENDING,
    )


def test_copy_single_file(tmp_path: Path, worker_copy) -> None:
    src = tmp_path / "src" / "hello.txt"
    src.parent.mkdir()
    src.write_text("hello world")

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    op = _make_op(src, dest_dir)
    result = OperationResult()

    worker_copy._process_file(op, result)

    assert (dest_dir / "hello.txt").read_text() == "hello world"
    assert src.exists(), "copy must leave the source in place"
    assert result.success_count == 1
    assert result.total_bytes == len("hello world")


def test_move_single_file(tmp_path: Path, worker_move) -> None:
    src = tmp_path / "src" / "moveme.txt"
    src.parent.mkdir()
    src.write_text("payload")

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    op = _make_op(src, dest_dir)
    result = OperationResult()

    worker_move._process_file(op, result)

    assert (dest_dir / "moveme.txt").read_text() == "payload"
    assert not src.exists(), "move must remove the source"
    assert result.success_count == 1


def test_copy_renames_on_collision(tmp_path: Path, worker_copy) -> None:
    src = tmp_path / "src" / "doc.txt"
    src.parent.mkdir()
    src.write_text("new")

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    (dest_dir / "doc.txt").write_text("existing")

    op = _make_op(src, dest_dir)
    result = OperationResult()

    worker_copy._process_file(op, result)

    assert (dest_dir / "doc.txt").read_text() == "existing"
    assert (dest_dir / "doc (1).txt").read_text() == "new"
    assert result.success_count == 1


def test_copy_directory_recursive(tmp_path: Path, worker_copy) -> None:
    src = tmp_path / "src" / "tree"
    (src / "sub").mkdir(parents=True)
    (src / "top.txt").write_text("top")
    (src / "sub" / "nested.txt").write_text("nested")

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    op = FileOperation(
        source=src,
        destination=dest_dir / src.name,
        mode=OperationMode.COPY,
        status=OperationStatus.PENDING,
    )
    result = OperationResult()

    worker_copy._process_directory(op, result)

    assert (dest_dir / "tree" / "top.txt").read_text() == "top"
    assert (dest_dir / "tree" / "sub" / "nested.txt").read_text() == "nested"
    assert src.exists(), "copy must leave the source tree intact"
    assert result.success_count == 1


def test_move_directory_recursive(tmp_path: Path, worker_move) -> None:
    src = tmp_path / "src" / "moveable_tree"
    (src / "inner").mkdir(parents=True)
    (src / "a.txt").write_text("a")
    (src / "inner" / "b.txt").write_text("b")

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    op = FileOperation(
        source=src,
        destination=dest_dir / src.name,
        mode=OperationMode.MOVE,
        status=OperationStatus.PENDING,
    )
    result = OperationResult()

    # Collect log messages so we can assert the item count survives the move
    log_messages: list[str] = []
    worker_move.log_message.connect(log_messages.append)

    worker_move._process_directory(op, result)

    assert (dest_dir / "moveable_tree" / "a.txt").read_text() == "a"
    assert (dest_dir / "moveable_tree" / "inner" / "b.txt").read_text() == "b"
    assert not src.exists(), "move must remove the source tree"
    assert result.success_count == 1

    # rglob('*') sees a.txt, inner, inner/b.txt → 3 entries. Before the M4
    # fix the count was taken after the move and silently came out as 0.
    success_line = next(m for m in log_messages if m.startswith("✓ Moved"))
    assert "(3 items)" in success_line


def test_copy_preserves_mtime(tmp_path: Path, worker_copy) -> None:
    import os
    import time

    src = tmp_path / "src" / "old.txt"
    src.parent.mkdir()
    src.write_text("content")

    # Set mtime to a known historical value
    past = time.time() - 7 * 24 * 3600  # 1 week ago
    os.utime(src, (past, past))

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    op = _make_op(src, dest_dir)
    result = OperationResult()

    worker_copy._process_file(op, result)

    copied = dest_dir / "old.txt"
    # shutil.copy2 preserves mtime within filesystem granularity
    assert abs(copied.stat().st_mtime - past) < 2.0


def test_chunked_copy_for_large_file(tmp_path: Path, worker_copy) -> None:
    # File just over 10MB triggers the chunked-copy branch
    src = tmp_path / "src" / "big.bin"
    src.parent.mkdir()
    payload = b"x" * (10 * 1024 * 1024 + 1024)  # 10 MB + 1 KB
    src.write_bytes(payload)

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    op = _make_op(src, dest_dir)
    result = OperationResult()

    worker_copy._process_file(op, result)

    assert (dest_dir / "big.bin").read_bytes() == payload
    assert result.success_count == 1
    assert result.total_bytes == len(payload)
