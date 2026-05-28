"""Tests for FileOperationWorker._get_unique_destination."""
from __future__ import annotations

from pathlib import Path

from my_dropper_app.app import FileOperationWorker

# The method does not touch `self` — calling it as an unbound method with
# a None receiver is intentional and keeps these tests pure-logic.
_unique = FileOperationWorker._get_unique_destination


def test_returns_original_when_no_collision(tmp_path: Path) -> None:
    target = tmp_path / "fresh.txt"
    assert _unique(None, target) == target


def test_appends_1_on_first_collision(tmp_path: Path) -> None:
    existing = tmp_path / "report.txt"
    existing.write_text("first")

    result = _unique(None, existing)

    assert result == tmp_path / "report (1).txt"
    assert not result.exists()


def test_sequential_collisions(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text("a")
    (tmp_path / "doc (1).md").write_text("b")
    (tmp_path / "doc (2).md").write_text("c")

    result = _unique(None, tmp_path / "doc.md")

    assert result == tmp_path / "doc (3).md"


def test_extensionless_file(tmp_path: Path) -> None:
    existing = tmp_path / "Makefile"
    existing.write_text("all:")

    result = _unique(None, existing)

    assert result == tmp_path / "Makefile (1)"


def test_multi_dot_filename(tmp_path: Path) -> None:
    existing = tmp_path / "archive.tar.gz"
    existing.write_text("blob")

    result = _unique(None, existing)

    # Path.stem strips only the final suffix, so "archive.tar.gz" → stem
    # "archive.tar", suffix ".gz". The collision-renamer reflects that.
    assert result == tmp_path / "archive.tar (1).gz"


def test_directory_collision(tmp_path: Path) -> None:
    existing = tmp_path / "photos"
    existing.mkdir()

    result = _unique(None, existing)

    assert result == tmp_path / "photos (1)"
    assert not result.exists()
