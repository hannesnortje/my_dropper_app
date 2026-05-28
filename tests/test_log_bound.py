"""Tests for the bounded activity log.

A bulk operation of tens of thousands of items previously grew the
QTextDocument unbounded — eventually visible in RAM usage. The log
document is now capped via setMaximumBlockCount(MAX_LOG_LINES).
"""
from __future__ import annotations

import pytest

pytest.importorskip("pytestqt")

from my_dropper_app.constants import MAX_LOG_LINES


def test_max_block_count_is_set_on_the_document(qtbot) -> None:
    from my_dropper_app.app import FileDropperApp

    widget = FileDropperApp()
    qtbot.addWidget(widget)

    assert widget.output_text.document().maximumBlockCount() == MAX_LOG_LINES


def test_appending_past_the_cap_does_not_exceed_it(qtbot) -> None:
    """Push the log well past its cap and verify Qt auto-trimmed."""
    from my_dropper_app.app import FileDropperApp

    widget = FileDropperApp()
    qtbot.addWidget(widget)

    overshoot = 200
    for i in range(MAX_LOG_LINES + overshoot):
        widget._log(f"line {i}")

    block_count = widget.output_text.document().blockCount()
    assert block_count <= MAX_LOG_LINES, (
        f"blockCount={block_count} exceeded cap {MAX_LOG_LINES}"
    )


def test_most_recent_lines_are_retained(qtbot) -> None:
    """When trimming kicks in, the *newest* lines must survive — losing
    the head of the log is fine, losing the tail would hide recent
    errors from the user."""
    from my_dropper_app.app import FileDropperApp

    widget = FileDropperApp()
    qtbot.addWidget(widget)

    for i in range(MAX_LOG_LINES + 50):
        widget._log(f"line {i}")

    text = widget.output_text.toPlainText()
    # Last line written must still be visible
    assert f"line {MAX_LOG_LINES + 49}" in text
    # First lines should have been discarded
    assert "line 0" not in text
    assert "line 1\n" not in text
