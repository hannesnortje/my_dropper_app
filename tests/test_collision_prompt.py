"""Tests for the Replace / Keep both / Cancel collision prompt.

The text-drop tests exercise FileDropperApp._process_dropped_text with a
known payload that produces a deterministic filename
(`<modelId>.scenario.json`), then pre-create that file and monkeypatch
`_prompt_collision` to simulate each user choice.

The worker tests exercise the wait/wake plumbing on
FileOperationWorker — including the apply-to-all caching and the
mid-wait cancellation path — without spinning up a real QThread.
"""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from PyQt6.QtWidgets import QMessageBox

from my_dropper_app.app import FileDropperApp
from my_dropper_app.models import (
    CollisionAction,
    FileOperation,
    OperationMode,
    OperationResult,
)
from my_dropper_app.worker import FileOperationWorker


# -----------------------------------------------------------------------------
# Shared helpers
# -----------------------------------------------------------------------------

# JSON whose modelId is known, so parse_text_for_filename returns
# ("scenario1.scenario", "json") → on-disk name "scenario1.scenario.json".
SCENARIO_TEXT_V1 = '{"ior": {"modelId": "scenario1"}}'
SCENARIO_TEXT_V2 = '{"ior": {"modelId": "scenario1"}, "version": "v2"}'
EXPECTED_FILENAME = "scenario1.scenario.json"


def _silence_modal_dialogs(monkeypatch) -> None:
    """Stub out the success/failure dialogs so tests don't block on UI."""
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **kw: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **kw: None)


def _make_app(tmp_path: Path, qapp) -> FileDropperApp:
    app = FileDropperApp()
    app.destination_directory = tmp_path
    return app


# -----------------------------------------------------------------------------
# Text-drop path
# -----------------------------------------------------------------------------

def test_text_drop_replace_overwrites_existing(
    tmp_path: Path, qapp, monkeypatch
) -> None:
    _silence_modal_dialogs(monkeypatch)
    app = _make_app(tmp_path, qapp)

    existing = tmp_path / EXPECTED_FILENAME
    existing.write_text("OLD CONTENT")

    monkeypatch.setattr(
        app, "_prompt_collision", lambda name: CollisionAction.REPLACE
    )

    app._process_dropped_text(SCENARIO_TEXT_V2)

    # Original filename still present, but with the NEW contents
    assert existing.exists()
    assert SCENARIO_TEXT_V2 in existing.read_text()
    assert "OLD CONTENT" not in existing.read_text()
    # No _001 sibling was created
    assert not (tmp_path / "scenario1.scenario_001.json").exists()


def test_text_drop_keep_both_creates_suffixed_copy(
    tmp_path: Path, qapp, monkeypatch
) -> None:
    _silence_modal_dialogs(monkeypatch)
    app = _make_app(tmp_path, qapp)

    existing = tmp_path / EXPECTED_FILENAME
    existing.write_text("OLD CONTENT")

    monkeypatch.setattr(
        app, "_prompt_collision", lambda name: CollisionAction.KEEP_BOTH
    )

    app._process_dropped_text(SCENARIO_TEXT_V2)

    # Original untouched
    assert existing.read_text() == "OLD CONTENT"
    # _001 sibling appears with the NEW contents
    sibling = tmp_path / "scenario1.scenario_001.json"
    assert sibling.exists()
    assert SCENARIO_TEXT_V2 in sibling.read_text()


def test_text_drop_cancel_writes_nothing(
    tmp_path: Path, qapp, monkeypatch
) -> None:
    _silence_modal_dialogs(monkeypatch)
    app = _make_app(tmp_path, qapp)

    existing = tmp_path / EXPECTED_FILENAME
    existing.write_text("OLD CONTENT")

    monkeypatch.setattr(
        app, "_prompt_collision", lambda name: CollisionAction.CANCEL
    )

    log_lines: list[str] = []
    monkeypatch.setattr(app, "_log", log_lines.append)

    app._process_dropped_text(SCENARIO_TEXT_V2)

    # No new file, original untouched
    assert existing.read_text() == "OLD CONTENT"
    assert not (tmp_path / "scenario1.scenario_001.json").exists()
    # And the skip is logged so the user knows why nothing happened
    assert any("Skipped (user chose to cancel)" in line for line in log_lines), \
        log_lines


# -----------------------------------------------------------------------------
# Worker plumbing
# -----------------------------------------------------------------------------

def test_resolve_collision_returns_cancel_when_cancel_fires_during_wait(
    qapp,
) -> None:
    """The wait loop polls _cancelled every 100 ms. A cancel from another
    thread while the user is still staring at the prompt must let the
    worker abort cleanly instead of blocking forever.
    """
    worker = FileOperationWorker(operations=[], mode=OperationMode.COPY)
    # Connect a no-op slot so receivers() > 0 and _resolve_collision takes
    # the prompt-and-wait path. Without a listener it would short-circuit
    # to KEEP_BOTH (used by headless callers like the existing collision
    # tests in test_file_ops.py).
    worker.collision_detected.connect(lambda s, d: None)

    captured: dict[str, CollisionAction] = {}

    def run_resolver():
        captured["action"] = worker._resolve_collision(
            Path("/tmp/source"), Path("/tmp/dest")
        )

    t = threading.Thread(target=run_resolver)
    t.start()
    # Let the resolver enter the wait loop, then trigger cancellation.
    time.sleep(0.05)
    worker.cancel()
    t.join(timeout=2.0)

    assert not t.is_alive(), "resolver did not exit on cancellation"
    assert captured["action"] == CollisionAction.CANCEL


def test_resolve_destination_replace_removes_existing_directory(
    tmp_path: Path, qapp
) -> None:
    """REPLACE on a directory destination must rmtree the existing tree
    so the subsequent copytree lands cleanly. The shutil docs are clear
    that copytree refuses to write into an existing directory.
    """
    worker = FileOperationWorker(operations=[], mode=OperationMode.COPY)

    src = tmp_path / "src"
    src.mkdir()
    (src / "new.txt").write_text("new")

    dest = tmp_path / "dest" / "src"
    dest.mkdir(parents=True)
    (dest / "old.txt").write_text("old")
    assert dest.is_dir()
    assert (dest / "old.txt").exists()

    op = FileOperation(source=src, destination=dest, mode=OperationMode.COPY)
    result = OperationResult()

    # Pre-arm an apply-to-all REPLACE so _resolve_collision returns
    # immediately without emitting (no UI thread is running this test).
    worker._collision_action = CollisionAction.REPLACE
    worker._collision_apply_to_all = True

    resolved = worker._resolve_destination(op, result)

    assert resolved == dest
    assert not dest.exists(), "existing directory should have been removed"
    assert result.skipped_count == 0
    assert result.fail_count == 0


def test_apply_to_all_reuses_cached_answer_without_emitting(
    qapp,
) -> None:
    """First collision: emit, wait, get answer. With apply_to_all=True
    set, subsequent collisions must return the cached choice and skip
    the signal entirely so a 100-file batch doesn't pop 100 dialogs.
    """
    worker = FileOperationWorker(operations=[], mode=OperationMode.COPY)

    emissions: list[tuple[Path, Path]] = []
    worker.collision_detected.connect(
        lambda s, d: emissions.append((s, d))
    )

    # Simulate the user's first answer being "Replace, apply to all".
    worker._collision_action = CollisionAction.REPLACE
    worker._collision_apply_to_all = True

    a1 = worker._resolve_collision(Path("/s/a"), Path("/d/a"))
    a2 = worker._resolve_collision(Path("/s/b"), Path("/d/b"))
    a3 = worker._resolve_collision(Path("/s/c"), Path("/d/c"))

    assert a1 == a2 == a3 == CollisionAction.REPLACE
    assert emissions == [], (
        "no signal emissions expected when apply_to_all is active; got "
        f"{emissions}"
    )
