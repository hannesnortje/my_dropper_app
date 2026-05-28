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

    # Each tuple: (attribute path on widget, human label, expect_tooltip)
    # progress_bar and output_text are displays, not controls — no tooltip
    # expected. Everything else is hover-discoverable.
    expected = [
        ("dark_mode_checkbox",   "dark mode checkbox",     True),
        ("destination_combo",    "destination combo",      True),
        ("open_dest_button",     "open-destination button", True),
        ("copy_radio",           "copy radio",             True),
        ("move_radio",           "move radio",             True),
        ("drop_label",           "drop zone label",        True),
        ("cancel_button",        "cancel button",          True),
        ("progress_bar",         "progress bar",           False),
        ("output_text",          "output log",             False),
    ]

    for attr, label, expect_tooltip in expected:
        target = getattr(widget, attr)
        name = target.accessibleName()
        desc = target.accessibleDescription()
        assert name, f"{label} has no accessibleName"
        assert desc, f"{label} has no accessibleDescription"
        if expect_tooltip:
            assert target.toolTip(), f"{label} has no toolTip"
