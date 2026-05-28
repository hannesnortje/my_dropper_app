"""Smoke test: every interactive widget has accessibleName/Description set.

We construct a real FileDropperApp under the offscreen Qt platform and
assert that each named widget has non-empty a11y attributes. This guards
against future changes that introduce a new widget without wiring up
its screen-reader text.
"""
from __future__ import annotations

import pytest

pytest.importorskip("pytestqt")


def test_every_interactive_widget_has_accessibility_metadata(qtbot) -> None:
    from my_dropper_app.app import FileDropperApp

    widget = FileDropperApp()
    qtbot.addWidget(widget)

    # Each tuple: (attribute path on widget, human label for assertion error)
    expected = [
        ("dark_mode_checkbox",   "dark mode checkbox"),
        ("destination_combo",    "destination combo"),
        ("open_dest_button",     "open-destination button"),
        ("copy_radio",           "copy radio"),
        ("move_radio",           "move radio"),
        ("drop_label",           "drop zone label"),
        ("cancel_button",        "cancel button"),
        ("progress_bar",         "progress bar"),
        ("output_text",          "output log"),
    ]

    for attr, label in expected:
        target = getattr(widget, attr)
        name = target.accessibleName()
        desc = target.accessibleDescription()
        assert name, f"{label} has no accessibleName"
        assert desc, f"{label} has no accessibleDescription"
