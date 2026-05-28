"""Regression test for the drop-label object-name lifecycle.

Before Phase 5.4 the `_apply_theme` method unconditionally reset
`drop_label.setObjectName("dropLabel")` and then forced a self-set
stylesheet to repolish. That meant any caller that set the object
name to "dropLabelActive" immediately before calling `_apply_theme`
would have it silently reset — so the drag-active state never
actually showed on screen.

After the cleanup, `_apply_theme` only applies the global stylesheet
and leaves child object names alone, so the active state survives.
"""
from __future__ import annotations

import pytest

pytest.importorskip("pytestqt")


def test_apply_theme_does_not_reset_drop_label_object_name(qtbot) -> None:
    from my_dropper_app.app import FileDropperApp

    widget = FileDropperApp()
    qtbot.addWidget(widget)

    # Simulate the dragEnterEvent flow: caller flips object name, then
    # calls _apply_theme to repolish.
    widget.drop_label.setObjectName("dropLabelActive")
    widget._apply_theme()

    assert widget.drop_label.objectName() == "dropLabelActive", (
        "_apply_theme must leave the drop label's object name alone "
        "so drag-active styling can show"
    )


def test_apply_theme_keeps_default_state_when_unchanged(qtbot) -> None:
    """A bare _apply_theme call (e.g. dark-mode toggle while idle) must
    not change the drop label's object name from its default."""
    from my_dropper_app.app import FileDropperApp

    widget = FileDropperApp()
    qtbot.addWidget(widget)

    assert widget.drop_label.objectName() == "dropLabel"
    widget._apply_theme()
    assert widget.drop_label.objectName() == "dropLabel"
