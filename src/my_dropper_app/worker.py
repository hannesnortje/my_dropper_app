"""Background QThread worker that performs file copy / move operations.

Kept separate from app.py so the UI widget can stay focused on UI. The
worker has no widget references — it emits signals which the widget
connects to its slots, and reads its cancellation flag via a
threading.Event for cross-platform thread safety.
"""
from __future__ import annotations

import logging
import shutil
import threading
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from .constants import COPY_CHUNK_SIZE, LARGE_FILE_THRESHOLD
from .models import CollisionAction, FileOperation, OperationMode, OperationResult
from .parsing import get_unique_destination

logger = logging.getLogger(__name__)


class FileOperationWorker(QThread):
    """Worker thread for performing file operations without blocking UI."""

    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    operation_completed = pyqtSignal(OperationResult)
    log_message = pyqtSignal(str)
    # Emitted from the worker thread when a destination already exists. The
    # UI slot pops a Replace / Keep both / Cancel dialog and feeds the
    # answer back via set_collision_response(). The worker blocks on
    # _collision_event in between.
    collision_detected = pyqtSignal(Path, Path)  # source, destination

    def __init__(
        self,
        operations: List[FileOperation],
        mode: OperationMode,
        parent: Optional[QThread] = None,
    ):
        super().__init__(parent)
        self.operations = operations
        self.mode = mode
        # threading.Event gives an explicit cross-thread happens-before
        # relationship rather than relying on CPython-specific atomicity
        # of a bare bool.
        self._cancelled = threading.Event()
        # Collision-prompt plumbing. The worker emits collision_detected,
        # waits on _collision_event for the UI thread to call
        # set_collision_response(), then reads _collision_action.
        self._collision_event = threading.Event()
        self._collision_action: Optional[CollisionAction] = None
        self._collision_apply_to_all: bool = False

    def cancel(self) -> None:
        """Request cancellation of the operation."""
        self._cancelled.set()
        # Wake any thread blocked in _resolve_collision so it can observe
        # the cancellation and return CANCEL promptly.
        self._collision_event.set()
        logger.info("File operation cancellation requested")

    def is_cancelled(self) -> bool:
        """Return True if cancellation has been requested."""
        return self._cancelled.is_set()

    def set_collision_response(
        self,
        action: CollisionAction,
        apply_to_all: bool = False,
    ) -> None:
        """Called from the UI thread after the user answers the prompt.

        Stores the chosen action (and whether it should be reused for the
        rest of this batch) and unblocks _resolve_collision.
        """
        self._collision_action = action
        self._collision_apply_to_all = apply_to_all
        self._collision_event.set()

    def _resolve_collision(self, source: Path, dest: Path) -> CollisionAction:
        """Block until the UI thread answers the collision prompt.

        If the user previously ticked "Apply to all remaining", the cached
        answer is reused without prompting again. If cancellation is
        requested mid-wait, returns CANCEL so the caller can skip the
        item cleanly. If no UI slot is connected to collision_detected
        (headless tests, scripted use), fall back to KEEP_BOTH so the
        worker doesn't block waiting for a reply that will never come.
        """
        if self._collision_apply_to_all and self._collision_action is not None:
            return self._collision_action

        # No listener → preserve the pre-prompt behaviour (auto-rename via
        # get_unique_destination, which is what KEEP_BOTH triggers in the
        # caller).
        if self.receivers(self.collision_detected) == 0:
            return CollisionAction.KEEP_BOTH

        self._collision_event.clear()
        self._collision_action = None
        self.collision_detected.emit(source, dest)

        # Poll loop — short timeout so an Esc / window-close mid-prompt
        # is observed within ~100 ms even if the user never clicks a
        # button. cancel() also sets _collision_event so the wait exits
        # immediately in that case.
        while not self._collision_event.is_set():
            if self._cancelled.is_set():
                return CollisionAction.CANCEL
            self._collision_event.wait(timeout=0.1)

        if self._cancelled.is_set():
            return CollisionAction.CANCEL
        return self._collision_action or CollisionAction.KEEP_BOTH

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
                # is_symlink() must come first — is_file() and is_dir()
                # silently follow symlinks, which would copy the target
                # (potentially recursing into a loop) without the user
                # ever knowing they dropped a symlink.
                if op.source.is_symlink():
                    self.log_message.emit(
                        f"⏭ Skipped symlink (not followed): {op.source.name}"
                    )
                    result.skipped_count += 1
                elif op.source.is_file():
                    self._process_file(op, result)
                elif op.source.is_dir():
                    self._process_directory(op, result)
                else:
                    self.log_message.emit(f"⚠️ Skipping unsupported item: {op.source.name}")
                    result.skipped_count += 1
            except PermissionError as e:
                self.log_message.emit(f"❌ Permission denied: {op.source.name}")
                result.fail_count += 1
                result.errors.append(str(e))
            except FileNotFoundError as e:
                self.log_message.emit(f"❌ File not found: {op.source.name}")
                result.fail_count += 1
                result.errors.append(str(e))
            except shutil.Error as e:
                self.log_message.emit(f"❌ File operation error: {op.source.name} - {e}")
                result.fail_count += 1
                result.errors.append(str(e))
            except RuntimeError as e:
                # Raised by get_unique_destination when MAX_COLLISION_ATTEMPTS
                # is exhausted, and by _move_cross_filesystem on phase failure.
                self.log_message.emit(f"❌ {op.source.name}: {e}")
                result.fail_count += 1
                result.errors.append(str(e))
            except Exception as e:
                self.log_message.emit(f"❌ Unexpected error for {op.source.name}: {e}")
                result.fail_count += 1
                result.errors.append(str(e))
                logger.exception(f"Unexpected error processing {op.source}")

        self.progress_updated.emit(total_ops, total_ops, "Complete")
        self.operation_completed.emit(result)

    def _process_file(self, op: FileOperation, result: OperationResult) -> None:
        """Process a single file operation."""
        dest_path = self._resolve_destination(op, result)
        if dest_path is None:
            return  # user chose Cancel for this item
        file_size = op.source.stat().st_size

        if self.mode == OperationMode.COPY:
            # Use chunked copy for progress on large files
            if file_size > LARGE_FILE_THRESHOLD:
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
        dest_path = self._resolve_destination(op, result)
        if dest_path is None:
            return  # user chose Cancel for this item

        # Count items BEFORE the operation — after a successful move the
        # source no longer exists, so counting afterwards silently yields 0.
        item_count = sum(1 for _ in op.source.rglob('*'))

        if self.mode == OperationMode.COPY:
            # symlinks=True preserves nested symlinks as symlinks rather than
            # following them, which prevents infinite recursion on circular
            # links and avoids silently bloating the destination.
            shutil.copytree(op.source, dest_path, symlinks=True)
            action = "Copied"
        else:
            self._safe_move(op.source, dest_path)
            action = "Moved"

        if dest_path.name != op.source.name:
            self.log_message.emit(
                f"✓ {action} directory (renamed): {op.source.name} → {dest_path.name} "
                f"({item_count} items)"
            )
        else:
            self.log_message.emit(f"✓ {action} directory: {op.source.name} ({item_count} items)")

        result.success_count += 1

    def _resolve_destination(
        self,
        op: FileOperation,
        result: OperationResult,
    ) -> Optional[Path]:
        """Resolve op.destination, prompting on collisions.

        Returns the path to write to (possibly with a " (N)" suffix), or
        None if the user chose Cancel — in which case `result` is updated
        and a log line is emitted so the caller can simply return.
        """
        if not op.destination.exists():
            return op.destination

        action = self._resolve_collision(op.source, op.destination)

        if action == CollisionAction.CANCEL:
            result.skipped_count += 1
            self.log_message.emit(
                f"⏭ Skipped (user chose to cancel): {op.source.name}"
            )
            return None

        if action == CollisionAction.REPLACE:
            # Remove the existing entry so copy/move lands cleanly.
            # rmtree on a non-empty directory is destructive — the prompt
            # default is Keep Both, so the user actively opted in.
            try:
                if op.destination.is_dir() and not op.destination.is_symlink():
                    shutil.rmtree(op.destination)
                else:
                    op.destination.unlink()
            except OSError as e:
                self.log_message.emit(
                    f"❌ Could not remove existing {op.destination.name}: {e}"
                )
                result.fail_count += 1
                result.errors.append(str(e))
                return None
            return op.destination

        # KEEP_BOTH — fall back to the existing rename-with-suffix flow
        return get_unique_destination(op.destination)

    def _chunked_copy(self, source: Path, dest: Path, total_size: int) -> None:
        """Copy file in chunks for better progress reporting."""
        chunk_size = COPY_CHUNK_SIZE
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
        # Phase 1: copy (preserve nested symlinks rather than following them)
        try:
            if source.is_dir():
                shutil.copytree(source, dest, symlinks=True)
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
        # Same FS — atomic os.rename via Path.rename
        source.rename(dest)
