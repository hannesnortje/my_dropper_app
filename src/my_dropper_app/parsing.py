"""Pure helpers for path validation, filename selection, and collision rename.

These functions deliberately have no Qt or `self` dependency so they can
be unit-tested without spinning up a widget. Where one of them produces
human-readable explanations (filename parsing), callers can pass a `log`
callback to receive them.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from .constants import MAX_COLLISION_ATTEMPTS


def validate_destination(path: Path) -> Optional[str]:
    """Return None if path is a usable destination, else a short reason.

    A "usable" destination must exist, be a directory, and be writable by
    the current process. The reason string is suitable for showing to a
    user in the log; do not parse it programmatically.
    """
    if not path.exists():
        return "does not exist"
    if not path.is_dir():
        return "not a directory"
    if not os.access(path, os.W_OK):
        return "no write permission"
    return None


def prune_stale_destinations(paths: List[str]) -> List[str]:
    """Return only paths that currently point at real directories.

    Order is preserved. Used at startup to drop entries from the
    recent-destinations list that no longer exist on disk, and on the
    fly when the user picks one that has since gone away.
    """
    return [p for p in paths if Path(p).is_dir()]


def get_unique_destination(dest: Path) -> Path:
    """Return `dest` if free, else `dest` with a " (N)" suffix that is.

    Raises RuntimeError if a free name cannot be found within
    MAX_COLLISION_ATTEMPTS — protects the worker thread from hanging
    when a destination has accumulated pathological collisions.
    """
    if not dest.exists():
        return dest

    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent

    for counter in range(1, MAX_COLLISION_ATTEMPTS + 1):
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate

    raise RuntimeError(
        f"Too many filename collisions for {dest.name}: "
        f"gave up after {MAX_COLLISION_ATTEMPTS} attempts"
    )


def parse_text_for_filename(
    text: str,
    log: Optional[Callable[[str], None]] = None,
) -> Tuple[str, str]:
    """Pick (filename_base, extension) for a dropped text payload.

    Recognises two domain shapes:
      - {"ior": {"modelId": "<str>"}} -> "<modelId>.scenario" / "json"
      - {"publicData": {"name": "<str>"}} -> "<safe_name>" / "ior"
    Anything else valid-JSON falls through to ("dropped_text", "json"),
    invalid JSON to ("dropped_text", "txt").

    If `log` is supplied it's called with a short explanation of the
    branch that fired. Wrong-type values (e.g. modelId as int) fall
    through silently rather than raising.
    """
    if log is None:
        def log(_msg: str) -> None:
            return

    filename_base = "dropped_text"
    extension = "txt"

    try:
        data = json.loads(text)

        if isinstance(data, dict):
            ior = data.get("ior")
            if isinstance(ior, dict):
                model_id = ior.get("modelId")
                if isinstance(model_id, str) and model_id.strip():
                    log(f"📌 Using modelId: {model_id}")
                    return f"{model_id}.scenario", "json"

            public_data = data.get("publicData")
            if isinstance(public_data, dict):
                name = public_data.get("name")
                if isinstance(name, str) and name.strip():
                    safe_name = "".join(
                        c for c in name
                        if c.isalnum() or c in (' ', '-', '_', '.')
                    ).strip()
                    if safe_name:
                        log(f"📌 Using name: {safe_name}")
                        return safe_name, "ior"

            extension = "json"
            log("📌 Saving as generic JSON")

    except json.JSONDecodeError:
        log("📌 Text is not JSON, saving as plain text")
    except Exception as e:  # noqa: BLE001 - intentional broad catch on user data
        log(f"⚠️ Error parsing text: {e}")

    return filename_base, extension
