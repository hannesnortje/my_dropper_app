"""Tests for FileOperationWorker cancellation semantics.

These verify the threading.Event-based cancellation flag wires through
both the per-op loop in run() and the chunked-copy inner loop. We
exercise the synchronous internals rather than QThread.start() so the
assertions are deterministic.
"""
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from my_dropper_app.app import (
    FileOperation,
    FileOperationWorker,
    OperationMode,
    OperationResult,
    OperationStatus,
)


@pytest.fixture
def worker(qapp):
    return FileOperationWorker(operations=[], mode=OperationMode.COPY)


def test_event_is_clear_at_construction(worker) -> None:
    assert not worker.is_cancelled()
    assert isinstance(worker._cancelled, threading.Event)


def test_cancel_sets_the_event(worker) -> None:
    worker.cancel()
    assert worker.is_cancelled()


def test_chunked_copy_aborts_when_pre_cancelled(tmp_path: Path, worker) -> None:
    src = tmp_path / "big.bin"
    src.write_bytes(b"x" * (2 * 1024 * 1024))  # 2 MB — two chunks
    dest = tmp_path / "out" / "big.bin"
    dest.parent.mkdir()

    # Cancel BEFORE invoking — the first loop iteration must observe the flag,
    # raise InterruptedError, and clean up the (possibly-empty) partial file.
    worker.cancel()

    with pytest.raises(InterruptedError):
        worker._chunked_copy(src, dest, total_size=src.stat().st_size)

    assert not dest.exists(), "partial file must be removed on cancellation"
    assert src.exists(), "source must be untouched"


def test_run_loop_short_circuits_when_pre_cancelled(
    tmp_path: Path, worker
) -> None:
    # Three trivial operations queued; cancelling before start should skip them all
    sources = []
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    for i in range(3):
        src = tmp_path / f"f{i}.txt"
        src.write_text(str(i))
        sources.append(src)

    worker.operations = [
        FileOperation(
            source=s,
            destination=dest_dir / s.name,
            mode=OperationMode.COPY,
            status=OperationStatus.PENDING,
        )
        for s in sources
    ]
    worker.cancel()

    # run() emits signals; with the qapp fixture from pytest-qt this is fine
    captured_results = []
    worker.operation_completed.connect(lambda r: captured_results.append(r))
    worker.run()

    assert len(captured_results) == 1
    result = captured_results[0]
    assert result.success_count == 0
    assert result.skipped_count == 3
    # No destination files should have been written
    for s in sources:
        assert not (dest_dir / s.name).exists()


def test_cancel_mid_chunked_copy_via_background_thread(
    tmp_path: Path, worker
) -> None:
    """Realistic race: cancel() fires from another thread while _chunked_copy
    is iterating. The Event makes the read in the worker observe the write
    from the canceller without relying on bare-bool atomicity.
    """
    # 50 MB source so the loop runs long enough for the background cancel
    # to land before EOF.
    src = tmp_path / "huge.bin"
    src.write_bytes(b"x" * (50 * 1024 * 1024))
    dest = tmp_path / "out.bin"

    def canceller():
        # Brief delay so the copy is in-flight when we cancel
        import time
        time.sleep(0.005)
        worker.cancel()

    t = threading.Thread(target=canceller)
    t.start()

    try:
        worker._chunked_copy(src, dest, total_size=src.stat().st_size)
        # If the file was small enough to finish first, that's a valid
        # outcome too — we only insist on either completion or clean abort.
        finished_cleanly = True
    except InterruptedError:
        finished_cleanly = False
    finally:
        t.join()

    if not finished_cleanly:
        assert not dest.exists(), "partial file must be cleaned on cancel"
    else:
        # If it completed, the destination should be a full byte-for-byte copy
        assert dest.stat().st_size == src.stat().st_size
