#!/usr/bin/env python3
"""
File Dropper & Saver Application (PyQt6)
Copyright (C) 2025

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This application uses PyQt6, which is licensed under the GPL.
"""
from __future__ import annotations

import sys
import os
import shutil
import json
import logging
import subprocess
import platform
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum, auto

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox, QFileDialog, QLineEdit, QProgressBar,
    QCheckBox, QFrame, QSizePolicy, QComboBox, QStyle
)
from PyQt6.QtCore import (
    Qt, QUrl, QEvent, pyqtSignal, QThread, QSettings, QSize, QPoint
)
from PyQt6.QtGui import (
    QDragEnterEvent, QDropEvent, QPalette, QColor, QFont, QIcon
)

# =============================================================================
# Constants & Configuration
# =============================================================================

try:
    from my_dropper_app import __version__
except ImportError:
    __version__ = "2.0.0"  # Fallback for direct script execution

APP_NAME = "File Dropper & Saver"
ORG_NAME = "CeruleanCircle"

# Settings keys
SETTINGS_DEST_DIR = "destination_directory"
SETTINGS_WINDOW_GEOMETRY = "window_geometry"
SETTINGS_WINDOW_STATE = "window_state"
SETTINGS_DARK_MODE = "dark_mode"
SETTINGS_OPERATION_MODE = "operation_mode"
SETTINGS_RECENT_DESTINATIONS = "recent_destinations"

# Default values
DEFAULT_DEST_DIR = Path.home() / "DroppedFiles_QT6"
MAX_RECENT_DESTINATIONS = 5
MAX_FILE_SIZE_WARNING_MB = 1000  # Warn if single file > 1GB
MAX_COLLISION_ATTEMPTS = 10_000  # Cap on " (N)" / "_NNN" filename rename attempts

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Pure helpers (no Qt / no self) — easy to unit-test
# =============================================================================

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


# =============================================================================
# Enums & Data Classes
# =============================================================================

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
    """Represents a single file operation."""
    source: Path
    destination: Path
    mode: OperationMode
    status: OperationStatus = OperationStatus.PENDING
    error: Optional[str] = None
    bytes_copied: int = 0
    total_bytes: int = 0


@dataclass
class OperationResult:
    """Result of a batch file operation."""
    success_count: int = 0
    fail_count: int = 0
    skipped_count: int = 0
    total_bytes: int = 0
    errors: List[str] = field(default_factory=list)


# =============================================================================
# Styles
# =============================================================================

LIGHT_STYLE = """
QWidget {
    font-family: 'Segoe UI', 'SF Pro Display', 'Ubuntu', sans-serif;
    font-size: 13px;
}

QMainWindow, QWidget#mainWidget {
    background-color: #fafafa;
}

QLabel#dropLabel {
    border: 3px dashed #b0b0b0;
    border-radius: 12px;
    background-color: #f5f5f5;
    padding: 30px;
    font-size: 16px;
    font-weight: 500;
    color: #555;
}

QLabel#dropLabel:hover {
    border-color: #888;
    background-color: #efefef;
}

QLabel#dropLabelActive {
    border: 3px dashed #2e7d32;
    border-radius: 12px;
    background-color: #e8f5e9;
    padding: 30px;
    font-size: 16px;
    font-weight: 500;
    color: #2e7d32;
}

QPushButton {
    background-color: #1976d2;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #1565c0;
}

QPushButton:pressed {
    background-color: #0d47a1;
}

QPushButton:disabled {
    background-color: #bdbdbd;
    color: #757575;
}

QPushButton#dangerButton {
    background-color: #d32f2f;
}

QPushButton#dangerButton:hover {
    background-color: #c62828;
}

QPushButton#secondaryButton {
    background-color: #f5f5f5;
    color: #333;
    border: 1px solid #ddd;
}

QPushButton#secondaryButton:hover {
    background-color: #eeeeee;
}

QLineEdit {
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 8px 12px;
    background-color: white;
}

QLineEdit:focus {
    border-color: #1976d2;
}

QTextEdit {
    border: 1px solid #ddd;
    border-radius: 8px;
    background-color: white;
    padding: 8px;
}

QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #e0e0e0;
    text-align: center;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #4caf50;
    border-radius: 4px;
}

QComboBox {
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 8px 12px;
    background-color: white;
    min-width: 100px;
}

QComboBox:focus {
    border-color: #1976d2;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #bdbdbd;
}

QCheckBox::indicator:checked {
    background-color: #1976d2;
    border-color: #1976d2;
}

QFrame#separator {
    background-color: #e0e0e0;
}
"""

DARK_STYLE = """
QWidget {
    font-family: 'Segoe UI', 'SF Pro Display', 'Ubuntu', sans-serif;
    font-size: 13px;
    color: #e0e0e0;
}

QMainWindow, QWidget#mainWidget {
    background-color: #1e1e1e;
}

QLabel#dropLabel {
    border: 3px dashed #555;
    border-radius: 12px;
    background-color: #2d2d2d;
    padding: 30px;
    font-size: 16px;
    font-weight: 500;
    color: #aaa;
}

QLabel#dropLabel:hover {
    border-color: #777;
    background-color: #333;
}

QLabel#dropLabelActive {
    border: 3px dashed #66bb6a;
    border-radius: 12px;
    background-color: #1b3d1f;
    padding: 30px;
    font-size: 16px;
    font-weight: 500;
    color: #81c784;
}

QPushButton {
    background-color: #0d7377;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #14a3a8;
}

QPushButton:pressed {
    background-color: #0a5c5f;
}

QPushButton:disabled {
    background-color: #404040;
    color: #666;
}

QPushButton#dangerButton {
    background-color: #c62828;
}

QPushButton#dangerButton:hover {
    background-color: #e53935;
}

QPushButton#secondaryButton {
    background-color: #333;
    color: #e0e0e0;
    border: 1px solid #444;
}

QPushButton#secondaryButton:hover {
    background-color: #404040;
}

QLineEdit {
    border: 1px solid #444;
    border-radius: 6px;
    padding: 8px 12px;
    background-color: #2d2d2d;
    color: #e0e0e0;
}

QLineEdit:focus {
    border-color: #0d7377;
}

QTextEdit {
    border: 1px solid #444;
    border-radius: 8px;
    background-color: #2d2d2d;
    color: #e0e0e0;
    padding: 8px;
}

QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #333;
    text-align: center;
    height: 20px;
    color: white;
}

QProgressBar::chunk {
    background-color: #0d7377;
    border-radius: 4px;
}

QComboBox {
    border: 1px solid #444;
    border-radius: 6px;
    padding: 8px 12px;
    background-color: #2d2d2d;
    color: #e0e0e0;
    min-width: 100px;
}

QComboBox:focus {
    border-color: #0d7377;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #e0e0e0;
    selection-background-color: #0d7377;
}

QCheckBox {
    spacing: 8px;
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #555;
    background-color: #2d2d2d;
}

QCheckBox::indicator:checked {
    background-color: #0d7377;
    border-color: #0d7377;
}

QFrame#separator {
    background-color: #444;
}

QMessageBox {
    background-color: #2d2d2d;
}

QMessageBox QLabel {
    color: #e0e0e0;
}
"""


# =============================================================================
# Worker Thread for File Operations
# =============================================================================

class FileOperationWorker(QThread):
    """Worker thread for performing file operations without blocking UI."""
    
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    operation_completed = pyqtSignal(OperationResult)
    log_message = pyqtSignal(str)
    
    def __init__(
        self,
        operations: List[FileOperation],
        mode: OperationMode,
        parent: Optional[QThread] = None
    ):
        super().__init__(parent)
        self.operations = operations
        self.mode = mode
        # threading.Event gives an explicit cross-thread happens-before
        # relationship rather than relying on CPython-specific atomicity
        # of a bare bool.
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        """Request cancellation of the operation."""
        self._cancelled.set()
        logger.info("File operation cancellation requested")

    def is_cancelled(self) -> bool:
        """Return True if cancellation has been requested."""
        return self._cancelled.is_set()
    
    def run(self) -> None:
        """Execute file operations in background."""
        result = OperationResult()
        total_ops = len(self.operations)
        
        for i, op in enumerate(self.operations):
            if self._cancelled.is_set():
                self.log_message.emit("⚠️ Operation cancelled by user")
                result.skipped_count = total_ops - i
                break
            
            self.progress_updated.emit(i, total_ops, f"Processing: {op.source.name}")
            
            try:
                if op.source.is_file():
                    self._process_file(op, result)
                elif op.source.is_dir():
                    self._process_directory(op, result)
                else:
                    self.log_message.emit(f"⚠️ Skipping unsupported item: {op.source.name}")
                    result.skipped_count += 1
                    
            except PermissionError as e:
                error_msg = f"❌ Permission denied: {op.source.name}"
                self.log_message.emit(error_msg)
                result.fail_count += 1
                result.errors.append(str(e))
            except FileNotFoundError as e:
                error_msg = f"❌ File not found: {op.source.name}"
                self.log_message.emit(error_msg)
                result.fail_count += 1
                result.errors.append(str(e))
            except shutil.Error as e:
                error_msg = f"❌ File operation error: {op.source.name} - {e}"
                self.log_message.emit(error_msg)
                result.fail_count += 1
                result.errors.append(str(e))
            except RuntimeError as e:
                # Raised by _get_unique_destination when MAX_COLLISION_ATTEMPTS
                # is exhausted; surface a clear, non-"unexpected" message.
                error_msg = f"❌ {op.source.name}: {e}"
                self.log_message.emit(error_msg)
                result.fail_count += 1
                result.errors.append(str(e))
            except Exception as e:
                error_msg = f"❌ Unexpected error for {op.source.name}: {e}"
                self.log_message.emit(error_msg)
                result.fail_count += 1
                result.errors.append(str(e))
                logger.exception(f"Unexpected error processing {op.source}")
        
        self.progress_updated.emit(total_ops, total_ops, "Complete")
        self.operation_completed.emit(result)
    
    def _process_file(self, op: FileOperation, result: OperationResult) -> None:
        """Process a single file operation."""
        dest_path = self._get_unique_destination(op.destination)
        file_size = op.source.stat().st_size
        
        if self.mode == OperationMode.COPY:
            # Use chunked copy for progress on large files
            if file_size > 10 * 1024 * 1024:  # > 10MB
                self._chunked_copy(op.source, dest_path, file_size)
            else:
                shutil.copy2(op.source, dest_path)
            action = "Copied"
        else:
            self._safe_move(op.source, dest_path)
            action = "Moved"

        if dest_path.name != op.source.name:
            self.log_message.emit(f"✓ {action} (renamed): {op.source.name} → {dest_path.name}")
        else:
            self.log_message.emit(f"✓ {action}: {op.source.name}")

        result.success_count += 1
        result.total_bytes += file_size
    
    def _process_directory(self, op: FileOperation, result: OperationResult) -> None:
        """Process a directory operation (recursive copy/move)."""
        dest_path = self._get_unique_destination(op.destination)

        if self.mode == OperationMode.COPY:
            shutil.copytree(op.source, dest_path)
            action = "Copied"
        else:
            self._safe_move(op.source, dest_path)
            action = "Moved"
        
        # Count items in directory
        item_count = sum(1 for _ in op.source.rglob('*'))
        
        if dest_path.name != op.source.name:
            self.log_message.emit(
                f"✓ {action} directory (renamed): {op.source.name} → {dest_path.name} "
                f"({item_count} items)"
            )
        else:
            self.log_message.emit(f"✓ {action} directory: {op.source.name} ({item_count} items)")
        
        result.success_count += 1
    
    def _chunked_copy(self, source: Path, dest: Path, total_size: int) -> None:
        """Copy file in chunks for better progress reporting."""
        chunk_size = 1024 * 1024  # 1MB chunks
        copied = 0
        
        with open(source, 'rb') as src, open(dest, 'wb') as dst:
            while True:
                if self._cancelled.is_set():
                    # Clean up partial file
                    dst.close()
                    dest.unlink(missing_ok=True)
                    raise InterruptedError("Operation cancelled")
                
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
                copied += len(chunk)
        
        # Copy metadata
        shutil.copystat(source, dest)

    @staticmethod
    def _is_cross_filesystem(source: Path, dest: Path) -> bool:
        """Return True if source and the destination's parent live on
        different filesystems (different st_dev values).

        On the same filesystem `os.rename` is atomic; across filesystems
        we must fall back to copy-then-delete and we want to know
        upfront so we can report which phase failed.
        """
        try:
            src_dev = source.stat().st_dev
            # The destination itself may not exist yet; its parent must.
            dst_dev = dest.parent.stat().st_dev
        except OSError:
            # If we can't even stat, defer to the cross-FS path which has
            # richer error handling than os.rename.
            return True
        return src_dev != dst_dev

    def _move_cross_filesystem(self, source: Path, dest: Path) -> None:
        """Move across filesystems with explicit copy → verify → delete.

        Each phase raises a phase-labelled RuntimeError on failure so the
        log line tells the user whether the source is preserved, the
        destination is corrupt, or the file now exists in BOTH locations.
        """
        # Phase 1: copy
        try:
            if source.is_dir():
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
        except Exception as e:
            # Clean up partial destination so we don't leave junk behind
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest, ignore_errors=True)
                else:
                    dest.unlink(missing_ok=True)
            raise RuntimeError(
                f"cross-filesystem copy failed (source preserved): {e}"
            ) from e

        # Phase 2: verify
        if not dest.exists():
            raise RuntimeError(
                "cross-filesystem copy reported success but destination is missing"
            )
        if source.is_file():
            src_size = source.stat().st_size
            dst_size = dest.stat().st_size
            if src_size != dst_size:
                # Corrupt copy — drop the destination so the source remains canonical
                dest.unlink(missing_ok=True)
                raise RuntimeError(
                    f"cross-filesystem copy size mismatch "
                    f"(src={src_size}, dst={dst_size}); destination removed"
                )

        # Phase 3: delete source
        try:
            if source.is_dir():
                shutil.rmtree(source)
            else:
                source.unlink()
        except Exception as e:
            raise RuntimeError(
                f"cross-filesystem copy succeeded but source delete failed — "
                f"file now exists in BOTH locations: {e}"
            ) from e

    def _safe_move(self, source: Path, dest: Path) -> None:
        """Move source → dest. Atomic rename on same filesystem; explicit
        copy-then-delete with phase-labelled errors across filesystems.
        """
        if self._is_cross_filesystem(source, dest):
            self._move_cross_filesystem(source, dest)
            return
        # Same FS — let Path.rename give us the atomic os.rename. For
        # consistency with shutil.move's prior behaviour we cast to str
        # internally; pathlib uses os.rename either way on POSIX.
        source.rename(dest)

    def _get_unique_destination(self, dest: Path) -> Path:
        """Get a unique destination path, renaming if necessary.

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


# =============================================================================
# Main Application Window
# =============================================================================

class FileDropperApp(QWidget):
    """Main application window for File Dropper & Saver."""
    
    def __init__(self):
        super().__init__()
        
        self.settings = QSettings(ORG_NAME, APP_NAME)
        self.worker: Optional[FileOperationWorker] = None
        self.is_dark_mode = self.settings.value(SETTINGS_DARK_MODE, False, type=bool)
        
        self._init_settings()
        self._init_ui()
        self._apply_theme()
        self._restore_geometry()
        
        logger.info(f"{APP_NAME} v{__version__} started")
    
    def _init_settings(self) -> None:
        """Initialize application settings."""
        self.destination_directory = Path(
            self.settings.value(SETTINGS_DEST_DIR, str(DEFAULT_DEST_DIR))
        )
        self.operation_mode = OperationMode.COPY
        mode_value = self.settings.value(SETTINGS_OPERATION_MODE, "copy")
        if mode_value == "move":
            self.operation_mode = OperationMode.MOVE
        
        raw_recents: List[str] = self.settings.value(
            SETTINGS_RECENT_DESTINATIONS, []
        ) or []
        self.recent_destinations = prune_stale_destinations(raw_recents)
        if len(self.recent_destinations) != len(raw_recents):
            # Persist the cleaned list so the user doesn't see ghosts next start
            self.settings.setValue(
                SETTINGS_RECENT_DESTINATIONS, self.recent_destinations
            )
            removed = [p for p in raw_recents if p not in self.recent_destinations]
            logger.info(f"Pruned stale recent destinations: {removed}")

        logger.info(f"Destination directory: {self.destination_directory}")
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle(f"{APP_NAME} (PyQt6)")
        self.setMinimumSize(700, 550)
        self.setObjectName("mainWidget")
        self.setAcceptDrops(True)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # Header with title and theme toggle
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"📁 {APP_NAME}")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.dark_mode_checkbox = QCheckBox("🌙 Dark Mode")
        self.dark_mode_checkbox.setChecked(self.is_dark_mode)
        self.dark_mode_checkbox.toggled.connect(self._toggle_dark_mode)
        header_layout.addWidget(self.dark_mode_checkbox)
        
        main_layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Settings section
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(12)
        
        dest_label = QLabel("Destination:")
        dest_label.setFixedWidth(80)
        settings_layout.addWidget(dest_label)
        
        self.destination_combo = QComboBox()
        self.destination_combo.setEditable(True)
        self.destination_combo.setMinimumWidth(300)
        self.destination_combo.lineEdit().setReadOnly(True)
        self._populate_recent_destinations()
        self.destination_combo.currentTextChanged.connect(self._on_destination_changed)
        settings_layout.addWidget(self.destination_combo, 1)
        
        browse_button = QPushButton("Browse...")
        browse_button.setObjectName("secondaryButton")
        browse_button.setFixedWidth(100)
        browse_button.clicked.connect(self._browse_destination)
        settings_layout.addWidget(browse_button)
        
        self.open_dest_button = QPushButton("📂 Open")
        self.open_dest_button.setObjectName("secondaryButton")
        self.open_dest_button.setFixedWidth(80)
        self.open_dest_button.setToolTip("Open destination folder")
        self.open_dest_button.clicked.connect(self._open_destination)
        settings_layout.addWidget(self.open_dest_button)
        
        main_layout.addLayout(settings_layout)
        
        # Operation mode selection
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(12)
        
        mode_label = QLabel("Mode:")
        mode_label.setFixedWidth(80)
        mode_layout.addWidget(mode_label)
        
        self.copy_radio = QCheckBox("📋 Copy files")
        self.copy_radio.setChecked(self.operation_mode == OperationMode.COPY)
        self.copy_radio.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.copy_radio)
        
        self.move_radio = QCheckBox("✂️ Move files")
        self.move_radio.setChecked(self.operation_mode == OperationMode.MOVE)
        self.move_radio.toggled.connect(lambda checked: self._on_mode_changed(not checked))
        mode_layout.addWidget(self.move_radio)
        
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)
        
        # Drop zone
        self.drop_label = QLabel("🎯 Drag & Drop Files or Text Here")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setObjectName("dropLabel")
        self.drop_label.setMinimumHeight(120)
        self.drop_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.drop_label)
        
        # Progress section
        self.progress_widget = QWidget()
        progress_layout = QVBoxLayout(self.progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)
        
        progress_header = QHBoxLayout()
        self.progress_label = QLabel("Ready")
        progress_header.addWidget(self.progress_label)
        progress_header.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("dangerButton")
        self.cancel_button.setFixedWidth(80)
        self.cancel_button.clicked.connect(self._cancel_operation)
        self.cancel_button.setVisible(False)
        progress_header.addWidget(self.cancel_button)
        
        progress_layout.addLayout(progress_header)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(self.progress_widget)
        
        # Output log
        self.output_text = QTextEdit()
        self.output_text.setPlaceholderText(
            "Dropped items and processing logs will appear here...\n\n"
            "💡 Tips:\n"
            "• Drag files or folders to copy/move them\n"
            "• Drag text to save it as a file\n"
            "• Use 'Move' mode to relocate files instead of copying"
        )
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)
        main_layout.addWidget(self.output_text)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        clear_button = QPushButton("🗑️ Clear Log")
        clear_button.setObjectName("secondaryButton")
        clear_button.clicked.connect(self.output_text.clear)
        button_layout.addWidget(clear_button)
        
        button_layout.addStretch()
        
        version_label = QLabel(f"v{__version__}")
        version_label.setStyleSheet("color: #888; font-size: 11px;")
        button_layout.addWidget(version_label)
        
        main_layout.addLayout(button_layout)
    
    def _populate_recent_destinations(self) -> None:
        """Populate the destination combo box with recent destinations."""
        self.destination_combo.clear()
        self.destination_combo.addItem(str(self.destination_directory))
        
        for dest in self.recent_destinations:
            if dest != str(self.destination_directory):
                self.destination_combo.addItem(dest)
    
    def _apply_theme(self) -> None:
        """Apply the current theme (light or dark)."""
        style = DARK_STYLE if self.is_dark_mode else LIGHT_STYLE
        self.setStyleSheet(style)
        
        # Update drop label style name based on state
        if hasattr(self, 'drop_label'):
            self.drop_label.setObjectName("dropLabel")
            self.drop_label.setStyleSheet(self.drop_label.styleSheet())
    
    def _toggle_dark_mode(self, enabled: bool) -> None:
        """Toggle dark mode on/off."""
        self.is_dark_mode = enabled
        self.settings.setValue(SETTINGS_DARK_MODE, enabled)
        self._apply_theme()
        logger.info(f"Dark mode {'enabled' if enabled else 'disabled'}")
    
    def _restore_geometry(self) -> None:
        """Restore window size and position from settings."""
        geometry = self.settings.value(SETTINGS_WINDOW_GEOMETRY)
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(750, 600)
            # Center on screen
            screen = QApplication.primaryScreen()
            if screen:
                screen_geo = screen.availableGeometry()
                x = (screen_geo.width() - self.width()) // 2
                y = (screen_geo.height() - self.height()) // 2
                self.move(x, y)
    
    def _save_geometry(self) -> None:
        """Save window size and position to settings."""
        self.settings.setValue(SETTINGS_WINDOW_GEOMETRY, self.saveGeometry())
    
    def _browse_destination(self) -> None:
        """Open dialog to select destination directory."""
        new_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Directory",
            str(self.destination_directory)
        )
        if new_dir:
            self._set_destination(new_dir)
    
    def _set_destination(self, path: str) -> None:
        """Set the destination directory and update UI."""
        self.destination_directory = Path(path)
        self.settings.setValue(SETTINGS_DEST_DIR, path)
        
        # Update recent destinations
        if path in self.recent_destinations:
            self.recent_destinations.remove(path)
        self.recent_destinations.insert(0, path)
        self.recent_destinations = self.recent_destinations[:MAX_RECENT_DESTINATIONS]
        self.settings.setValue(SETTINGS_RECENT_DESTINATIONS, self.recent_destinations)
        
        self._populate_recent_destinations()
        self._log(f"📁 Destination set to: {path}")
        logger.info(f"Destination changed to: {path}")
    
    def _on_destination_changed(self, text: str) -> None:
        """Handle destination combo box change.

        Validates the selected path and refuses to switch to one that
        doesn't exist, isn't a directory, or isn't writable. Without this
        check a stale entry in the recent-destinations dropdown would
        silently fail at the next drop.
        """
        if not text:
            return
        candidate = Path(text)
        error = validate_destination(candidate)
        if error is not None:
            self._log(f"⚠️ Cannot use destination ({error}): {text}")
            # If the stale entry is in recents, drop it so the user doesn't
            # keep tripping over the same ghost. Repopulate the combo
            # afterwards (with signals blocked to avoid re-entering here).
            if text in self.recent_destinations:
                self.recent_destinations.remove(text)
                self.settings.setValue(
                    SETTINGS_RECENT_DESTINATIONS, self.recent_destinations
                )
                self._log(f"🧹 Removed from recents: {text}")
            self.destination_combo.blockSignals(True)
            self._populate_recent_destinations()
            self.destination_combo.blockSignals(False)
            return
        self.destination_directory = candidate
        self.settings.setValue(SETTINGS_DEST_DIR, text)
    
    def _on_mode_changed(self, copy_checked: bool) -> None:
        """Handle operation mode change."""
        if copy_checked:
            self.operation_mode = OperationMode.COPY
            self.move_radio.setChecked(False)
        else:
            self.operation_mode = OperationMode.MOVE
            self.copy_radio.setChecked(False)
        
        mode_str = "copy" if self.operation_mode == OperationMode.COPY else "move"
        self.settings.setValue(SETTINGS_OPERATION_MODE, mode_str)
        logger.info(f"Operation mode changed to: {mode_str}")
    
    def _open_destination(self) -> None:
        """Open the destination directory in file manager."""
        path = self.destination_directory
        
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                self._log(f"📁 Created directory: {path}")
            except Exception as e:
                self._log(f"❌ Could not create directory: {e}")
                return
        
        system = platform.system()
        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", str(path)], check=True)
            elif system == "Windows":
                os.startfile(str(path))
            else:  # Linux
                subprocess.run(["xdg-open", str(path)], check=True)
            self._log(f"📂 Opened: {path}")
        except Exception as e:
            self._log(f"❌ Could not open directory: {e}")
            logger.exception("Failed to open destination directory")
    
    def _log(self, message: str) -> None:
        """Add message to the output log."""
        self.output_text.append(message)
    
    def _cancel_operation(self) -> None:
        """Cancel the current file operation."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Cancelling...")
    
    # =========================================================================
    # Drag and Drop Handling
    # =========================================================================
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
            self.drop_label.setObjectName("dropLabelActive")
            self._apply_theme()
            
            # Show what's being dragged
            if event.mimeData().hasUrls():
                count = len(event.mimeData().urls())
                self.drop_label.setText(f"🎯 Drop {count} item(s) here")
            else:
                self.drop_label.setText("🎯 Drop text here to save")
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event: QEvent) -> None:
        """Handle drag leave event."""
        self.drop_label.setObjectName("dropLabel")
        self.drop_label.setText("🎯 Drag & Drop Files or Text Here")
        self._apply_theme()
        event.accept()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event."""
        self.drop_label.setObjectName("dropLabel")
        self.drop_label.setText("🎯 Drag & Drop Files or Text Here")
        self._apply_theme()
        
        self._log("\n" + "─" * 50)
        self._log(f"📥 New Drop Event - {self.operation_mode.name} mode")
        self._log("─" * 50)
        
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_paths.append(Path(url.toLocalFile()))
                else:
                    self._log(f"⚠️ Skipping non-local URL: {url.toString()}")
            
            if file_paths:
                self._process_dropped_files(file_paths)
        elif event.mimeData().hasText():
            self._process_dropped_text(event.mimeData().text())
        else:
            self._log("❌ Dropped data format not supported")
            event.ignore()
            return
        
        event.acceptProposedAction()
    
    def _process_dropped_files(self, file_paths: List[Path]) -> None:
        """Process dropped files using worker thread."""
        self._log(f"📋 Received {len(file_paths)} item(s)")
        
        # Ensure destination exists
        try:
            self.destination_directory.mkdir(parents=True, exist_ok=True)
            self._log(f"📁 Destination: {self.destination_directory}")
        except OSError as e:
            self._log(f"❌ Cannot create destination: {e}")
            QMessageBox.critical(self, "Error", f"Cannot create destination directory:\n{e}")
            return
        
        # Check for large files
        total_size = sum(
            f.stat().st_size for f in file_paths if f.is_file()
        )
        if total_size > MAX_FILE_SIZE_WARNING_MB * 1024 * 1024:
            size_gb = total_size / (1024 * 1024 * 1024)
            reply = QMessageBox.question(
                self,
                "Large Transfer",
                f"You are about to {self.operation_mode.name.lower()} {size_gb:.1f} GB of data.\n"
                "This may take a while. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                self._log("⚠️ Operation cancelled by user")
                return
        
        # Create operations list
        operations = []
        for source in file_paths:
            dest = self.destination_directory / source.name
            operations.append(FileOperation(
                source=source,
                destination=dest,
                mode=self.operation_mode
            ))
        
        # Start worker thread
        self._start_worker(operations)
    
    def _start_worker(self, operations: List[FileOperation]) -> None:
        """Start the file operation worker thread."""
        self.worker = FileOperationWorker(operations, self.operation_mode)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.operation_completed.connect(self._on_operation_completed)
        self.worker.log_message.connect(self._log)
        
        # Show progress UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(operations))
        self.cancel_button.setVisible(True)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
        self.progress_label.setText("Starting...")
        
        # Disable drop zone during operation
        self.setAcceptDrops(False)
        
        self.worker.start()
    
    def _on_progress_updated(self, current: int, total: int, message: str) -> None:
        """Handle progress update from worker."""
        self.progress_bar.setValue(current)
        self.progress_bar.setMaximum(total)
        self.progress_label.setText(message)
    
    def _on_operation_completed(self, result: OperationResult) -> None:
        """Handle completion of file operations."""
        # Hide progress UI
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.progress_label.setText("Ready")
        
        # Re-enable drop zone
        self.setAcceptDrops(True)
        
        # Log summary
        self._log("─" * 50)
        mode_emoji = "📋" if self.operation_mode == OperationMode.COPY else "✂️"
        self._log(
            f"{mode_emoji} Complete: {result.success_count} succeeded, "
            f"{result.fail_count} failed, {result.skipped_count} skipped"
        )
        
        if result.total_bytes > 0:
            if result.total_bytes > 1024 * 1024 * 1024:
                size_str = f"{result.total_bytes / (1024*1024*1024):.2f} GB"
            elif result.total_bytes > 1024 * 1024:
                size_str = f"{result.total_bytes / (1024*1024):.1f} MB"
            else:
                size_str = f"{result.total_bytes / 1024:.1f} KB"
            self._log(f"📊 Total size: {size_str}")
        
        # Show completion message
        if result.fail_count == 0 and result.skipped_count == 0:
            QMessageBox.information(
                self,
                "Complete",
                f"Successfully {self.operation_mode.name.lower()}d {result.success_count} item(s)."
            )
        else:
            QMessageBox.warning(
                self,
                "Complete with Issues",
                f"Completed with {result.fail_count} failures and "
                f"{result.skipped_count} skipped items.\n\n"
                f"Check the log for details."
            )
        
        self.worker = None
    
    def _process_dropped_text(self, text_data: str) -> None:
        """Process dropped text data."""
        self._log(f"📝 Received text ({len(text_data)} characters)")
        
        # Ensure destination exists
        try:
            self.destination_directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self._log(f"❌ Cannot create destination: {e}")
            return
        
        # Determine filename from content
        filename_base, extension = self._parse_text_for_filename(text_data)

        # Generate unique filename (bounded to avoid hanging on pathological
        # destinations — see MAX_COLLISION_ATTEMPTS)
        file_path: Optional[Path] = None
        filename = ""
        for counter in range(MAX_COLLISION_ATTEMPTS + 1):
            if counter == 0:
                filename = f"{filename_base}.{extension}"
            else:
                filename = f"{filename_base}_{counter:03d}.{extension}"
            candidate = self.destination_directory / filename
            if not candidate.exists():
                file_path = candidate
                break

        if file_path is None:
            self._log(
                f"❌ Too many existing files like '{filename_base}.{extension}' "
                f"(>{MAX_COLLISION_ATTEMPTS}) — please clean up the destination."
            )
            QMessageBox.critical(
                self,
                "Too many collisions",
                f"Could not find a free filename after "
                f"{MAX_COLLISION_ATTEMPTS} attempts. Please clean up the "
                f"destination directory and try again.",
            )
            return

        # Save file
        try:
            file_path.write_text(text_data, encoding='utf-8')
            self._log(f"✓ Saved: {filename}")
            QMessageBox.information(
                self,
                "Text Saved",
                f"Successfully saved dropped text to:\n{filename}"
            )
        except Exception as e:
            self._log(f"❌ Error saving text: {e}")
            QMessageBox.critical(self, "Error", f"Could not save text:\n{e}")
    
    def _parse_text_for_filename(self, text: str) -> tuple[str, str]:
        """Parse text content to determine appropriate filename."""
        filename_base = "dropped_text"
        extension = "txt"
        
        try:
            data = json.loads(text)
            
            if isinstance(data, dict):
                # Check for ior.modelId
                if "ior" in data and isinstance(data["ior"], dict):
                    model_id = data["ior"].get("modelId", "")
                    if model_id and model_id.strip():
                        filename_base = f"{model_id}.scenario"
                        extension = "json"
                        self._log(f"📌 Using modelId: {model_id}")
                        return filename_base, extension
                
                # Check for publicData.name
                if "publicData" in data and isinstance(data["publicData"], dict):
                    name = data["publicData"].get("name", "")
                    if name and name.strip():
                        # Sanitize filename
                        safe_name = "".join(
                            c for c in name 
                            if c.isalnum() or c in (' ', '-', '_', '.')
                        ).strip()
                        if safe_name:
                            filename_base = safe_name
                            extension = "ior"
                            self._log(f"📌 Using name: {safe_name}")
                            return filename_base, extension
                
                # Generic JSON
                extension = "json"
                self._log("📌 Saving as generic JSON")
                
        except json.JSONDecodeError:
            self._log("📌 Text is not JSON, saving as plain text")
        except Exception as e:
            self._log(f"⚠️ Error parsing text: {e}")
        
        return filename_base, extension
    
    # =========================================================================
    # Window Events
    # =========================================================================
    
    def closeEvent(self, event: QEvent) -> None:
        """Handle window close event."""
        # Cancel any running operation
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Operation in Progress",
                "A file operation is still running. Cancel it and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.cancel()
                self.worker.wait(5000)  # Wait up to 5 seconds
            else:
                event.ignore()
                return
        
        # Save settings
        self._save_geometry()
        self.settings.setValue(SETTINGS_DEST_DIR, str(self.destination_directory))
        self.settings.sync()
        
        logger.info("Application closed")
        event.accept()


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationVersion(__version__)
    
    window = FileDropperApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
