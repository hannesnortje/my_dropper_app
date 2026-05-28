"""Data models for file operations.

Plain enums + dataclasses with no Qt dependency, so they can be imported
from anywhere — including pure-logic test paths — without dragging in
PyQt6 just to describe a file operation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional


class OperationMode(Enum):
    COPY = auto()
    MOVE = auto()


class OperationStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class FileOperation:
    """A single source → destination operation queued for the worker."""
    source: Path
    destination: Path
    mode: OperationMode
    status: OperationStatus = OperationStatus.PENDING
    error: Optional[str] = None
    bytes_copied: int = 0
    total_bytes: int = 0


@dataclass
class OperationResult:
    """Aggregated outcome of a batch of FileOperations."""
    success_count: int = 0
    fail_count: int = 0
    skipped_count: int = 0
    total_bytes: int = 0
    errors: List[str] = field(default_factory=list)
