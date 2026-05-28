"""Tests for drop-event routing logic.

These cover the helper that classifies what a drop is — local files,
text payload, or unsupported — without constructing a full QDropEvent.
The bug being fixed: a drag from a web source that uses a custom URL
scheme (e.g. "ior:local:...") carries a non-local URL AND a text/plain
JSON payload. Pre-fix, the URL branch was preferred unconditionally
and the text was never consulted.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from PyQt6.QtCore import QMimeData, QUrl

from my_dropper_app.app import FileDropperApp


def _mime_with_urls(*urls: str) -> QMimeData:
    m = QMimeData()
    m.setUrls([QUrl(u) for u in urls])
    return m


def _mime_with_urls_and_text(urls: list[str], text: str) -> QMimeData:
    m = _mime_with_urls(*urls)
    m.setText(text)
    return m


def test_local_file_url_is_extracted(tmp_path: Path, qapp) -> None:
    real = tmp_path / "a.txt"
    real.write_text("hi")
    mime = _mime_with_urls(QUrl.fromLocalFile(str(real)).toString())

    result = FileDropperApp._extract_local_files(mime)

    assert result == [real]


def test_custom_scheme_url_is_filtered_out(qapp) -> None:
    mime = _mime_with_urls(
        "ior:local:https://localhost:8443/EAMD.ucp/Components/foo.xml"
    )
    assert FileDropperApp._extract_local_files(mime) == []


def test_mixed_local_and_custom_keeps_only_local(tmp_path: Path, qapp) -> None:
    real = tmp_path / "real.txt"
    real.write_text("x")
    mime = _mime_with_urls(
        "ior:local:https://example.com/something",
        QUrl.fromLocalFile(str(real)).toString(),
    )
    assert FileDropperApp._extract_local_files(mime) == [real]


def test_no_urls_returns_empty(qapp) -> None:
    mime = QMimeData()
    mime.setText("just text, no urls")
    assert FileDropperApp._extract_local_files(mime) == []


def test_drop_with_custom_url_and_text_payload_uses_text(qapp) -> None:
    """The bug we're fixing: a web drag carrying both a custom URL and
    a JSON text/plain payload should route to the text handler, not
    silently ignore the drop.

    We exercise this by calling the helper and verifying the
    URL-extraction returns empty (so the caller's fallback to text
    triggers).
    """
    mime = _mime_with_urls_and_text(
        urls=[
            "ior:local:https://localhost:8443/EAMD.ucp/Components/"
            "com/canvas-gauges/CanvasGauges/1.0.0/CanvasGauges.component.xml"
        ],
        text='{"ior": {"modelId": "canvas-gauges-test"}}',
    )

    # URLs branch yields nothing (no local files)…
    assert FileDropperApp._extract_local_files(mime) == []
    # …and the mime still carries the JSON the text handler wants.
    assert mime.hasText()
    assert "modelId" in mime.text()
