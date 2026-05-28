"""Tests for the recent-destinations pruner."""
from __future__ import annotations

from pathlib import Path

from my_dropper_app.parsing import prune_stale_destinations


def test_empty_list_returns_empty() -> None:
    assert prune_stale_destinations([]) == []


def test_all_valid_directories_are_kept(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()

    result = prune_stale_destinations([str(a), str(b)])

    assert result == [str(a), str(b)]


def test_nonexistent_paths_are_dropped(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    ghost = tmp_path / "ghost"  # never created

    result = prune_stale_destinations([str(real), str(ghost)])

    assert result == [str(real)]


def test_files_masquerading_as_directories_are_dropped(tmp_path: Path) -> None:
    a_dir = tmp_path / "dir"
    a_dir.mkdir()
    a_file = tmp_path / "file.txt"
    a_file.write_text("nope")

    result = prune_stale_destinations([str(a_dir), str(a_file)])

    assert result == [str(a_dir)]


def test_order_is_preserved(tmp_path: Path) -> None:
    # Create them out of alphabetical order to confirm we don't sort
    z = tmp_path / "z"
    a = tmp_path / "a"
    m = tmp_path / "m"
    for d in (z, a, m):
        d.mkdir()

    result = prune_stale_destinations([str(z), str(a), str(m)])

    assert result == [str(z), str(a), str(m)]


def test_all_stale_returns_empty(tmp_path: Path) -> None:
    ghosts = [str(tmp_path / "g1"), str(tmp_path / "g2"), str(tmp_path / "g3")]
    assert prune_stale_destinations(ghosts) == []


def test_idempotent(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    ghost = tmp_path / "ghost"

    once = prune_stale_destinations([str(real), str(ghost)])
    twice = prune_stale_destinations(once)
    assert once == twice
