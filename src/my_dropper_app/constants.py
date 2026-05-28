"""Module-level constants and QSettings keys.

Single source of truth for tuning knobs (byte sizes, timeouts, caps) and
the strings used to read/write user preferences. Importing from here
rather than re-defining values in feature modules keeps drift impossible.
"""
from __future__ import annotations

from pathlib import Path

APP_NAME = "File Dropper & Saver"
ORG_NAME = "CeruleanCircle"

# QSettings keys
SETTINGS_DEST_DIR = "destination_directory"
SETTINGS_WINDOW_GEOMETRY = "window_geometry"
SETTINGS_DARK_MODE = "dark_mode"
SETTINGS_OPERATION_MODE = "operation_mode"
SETTINGS_RECENT_DESTINATIONS = "recent_destinations"

# Default values
DEFAULT_DEST_DIR = Path.home() / "DroppedFiles_QT6"
MAX_RECENT_DESTINATIONS = 5
MAX_COLLISION_ATTEMPTS = 10_000  # Cap on " (N)" / "_NNN" filename rename attempts

# Byte-size constants
BYTES_PER_KB = 1024
BYTES_PER_MB = 1024 * BYTES_PER_KB
BYTES_PER_GB = 1024 * BYTES_PER_MB

# Operation-tuning constants
COPY_CHUNK_SIZE = BYTES_PER_MB                    # 1 MB chunks in _chunked_copy
LARGE_FILE_THRESHOLD = 10 * BYTES_PER_MB          # switch to chunked copy above this
MAX_FILE_SIZE_WARNING_BYTES = 1000 * BYTES_PER_MB # confirm before transfers near 1 GB
WORKER_SHUTDOWN_TIMEOUT_MS = 5000                 # how long closeEvent waits for worker
