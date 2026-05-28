"""Tests for parsing.get_unique_destination."""
from __future__ import annotations

from pathlib import Path

import pytest

from my_dropper_app import parsing
from my_dropper_app.parsing import get_unique_destination


def _unique(_self, dest: Path) -> Path:
    """Backwards-compat shim so the existing tests keep the (None, path)
    call shape they used when this was an unbound method on the worker."""
    return get_unique_destination(dest)


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


def test_exhausting_max_attempts_raises_runtime_error(
    tmp_path: Path, monkeypatch
) -> None:
    # Shrink the cap so we can saturate it cheaply
    monkeypatch.setattr(parsing, "MAX_COLLISION_ATTEMPTS", 3)

    # Create the original plus all three collision slots (1), (2), (3)
    (tmp_path / "doc.txt").write_text("0")
    (tmp_path / "doc (1).txt").write_text("1")
    (tmp_path / "doc (2).txt").write_text("2")
    (tmp_path / "doc (3).txt").write_text("3")

    with pytest.raises(RuntimeError, match="Too many filename collisions"):
        _unique(None, tmp_path / "doc.txt")


def test_succeeds_at_boundary_of_max_attempts(
    tmp_path: Path, monkeypatch
) -> None:
    # With cap=3 and only (1) and (2) taken, (3) must succeed
    monkeypatch.setattr(parsing, "MAX_COLLISION_ATTEMPTS", 3)

    (tmp_path / "doc.txt").write_text("0")
    (tmp_path / "doc (1).txt").write_text("1")
    (tmp_path / "doc (2).txt").write_text("2")

    result = _unique(None, tmp_path / "doc.txt")

    assert result == tmp_path / "doc (3).txt"
    assert not result.exists()
