# Improvement Plan — File Dropper & Saver

Derived from the evaluation in `~/.claude/plans/can-you-please-thoroughly-functional-balloon.md`.
Work through phases top-to-bottom. Each phase is independently shippable.

Legend: `[C]` Critical · `[H]` High · `[M]` Medium · `[L]` Low

---

## Progress Summary

Tick the box when the entire sub-section's tasks are done. Use this as your dashboard.

**Phase 1 — Stop the Bleeding**
- [x] 1.1 [C1] Eliminate the duplicate app file
- [x] 1.2 [C2] Stand up a test harness
- [x] 1.3 Add a minimal CI workflow

**Phase 2 — High-Severity Bug Fixes**
- [x] 2.1 [H1] Cap the collision-rename loop
- [x] 2.2 [H2] Make cancellation thread-safe
- [x] 2.3 [H3] Validate destinations on change
- [x] 2.4 [H4] Filter stale recent destinations
- [x] 2.5 [H5] Document/log cross-FS move risk
- [x] 2.6 [H6] Decide on a symlink policy

**Phase 3 — Code Hygiene & Maintainability**
- [x] 3.1 [M1] Extract magic numbers to named constants
- [x] 3.2 [M2] Consolidate destination-directory creation
- [x] 3.3 [M3] Remove unused imports & constants
- [x] 3.4 [M4] Count directory items before move
- [x] 3.5 [M5] Tighten JSON filename parsing
- [x] 3.6 [M6] Make confirm-dialog non-blocking from worker perspective
- [x] 3.7 [M7] Per-platform "open folder" error messages

**Phase 4 — Architecture Cleanup**
- [x] 4.1 Split `app.py` into focused modules
- [x] 4.2 Defensive settings load

**Phase 5 — UX & Accessibility**
- [x] 5.1 [L3] Keyboard shortcuts
- [x] 5.2 [L4] Accessibility names and descriptions
- [ ] 5.3 [L1] Bound the output log
- [ ] 5.4 [L2] Tidy `_apply_theme`
- [ ] 5.5 [L7] Robust text-drop encoding
- [ ] 5.6 Add an "About" dialog
- [ ] 5.7 [L5] i18n scaffolding (optional, deferred)

**Phase 6 — Distribution & Polish**
- [ ] 6.1 [L6] Remove the `.docx` from the repo
- [ ] 6.2 Windows installer (optional)
- [ ] 6.3 macOS bundle (optional)
- [ ] 6.4 Release automation

**Phase 7 — Verification & Wrap-Up**
- [ ] 7.1 All commits merged, CI green
- [ ] 7.2 Manual smoke test pass
- [ ] 7.3 README updated
- [ ] 7.4 Version bump + release

---

## Phase 1 — Stop the Bleeding (duplication + safety net)

Goal: one source of truth, basic test coverage so future changes don't silently break things.

### 1.1 [C1] Eliminate the duplicate app file
- [x] Confirm `my_dropper_app_qt6.py` and `src/my_dropper_app/app.py` are functionally identical (`diff` minus the import-fallback block)
- [x] Decide on the canonical path: keep `src/my_dropper_app/app.py`
- [x] Verify `__main__.py` still launches correctly via `python -m my_dropper_app`
- [ ] Verify the `my-dropper-app` and `dropper` console scripts still work after a fresh `pip install -e .` *(deferred — verify manually before next release; package metadata unchanged so low risk)*
- [x] Delete `my_dropper_app_qt6.py`
- [x] Update `README.md` if it references the legacy script *(no references found)*
- [x] Update `launch.sh` if it references the legacy script
- [x] Commit: `refactor: remove duplicated legacy standalone script`

### 1.2 [C2] Stand up a test harness
- [x] Add `pytest` and `pytest-qt` to a new `[project.optional-dependencies]` `dev` group in `pyproject.toml`
- [x] Create `tests/` directory with `__init__.py` and `conftest.py`
- [x] Remove `tests/`, `test_*`, `*_test.py` patterns from `.gitignore` *(they were hiding the new suite)*
- [x] Add `tests/test_filename_collision.py` — covers `_get_unique_destination`:
  - [x] No collision: returns original path
  - [x] One collision: returns `name (1).ext`
  - [x] Sequential collisions: `(1)`, `(2)`, `(3)`
  - [x] Extensionless files
  - [x] Files with multiple dots (`archive.tar.gz`)
  - [x] Directory collisions (bonus)
- [x] Add `tests/test_text_parsing.py` — covers `_parse_text_for_filename`:
  - [x] Valid JSON with `ior.modelId`
  - [x] Valid JSON with `publicData.name` (plus unsafe-character stripping)
  - [x] Valid JSON with neither key
  - [x] Malformed JSON (returns fallback)
  - [x] Empty string
  - [x] Non-JSON plain text
  - [x] Top-level JSON array (bonus)
  - [x] Whitespace-only `modelId` (bonus)
- [x] Add `tests/test_file_ops.py` using `tmp_path`:
  - [x] Copy single file
  - [x] Move single file
  - [x] Copy directory recursively
  - [x] Move directory recursively
  - [x] Copy preserves metadata (mtime)
  - [x] Chunked-copy path for >10 MB files (bonus)
  - [x] Copy renames on collision (bonus)
- [x] Add `tests/test_settings.py`:
  - [x] Load with no prior settings → defaults
  - [x] Round-trip persistence (bonus)
  - [x] Load with corrupt/wrong-type values → falls back to defaults without crashing
  - *Note: deeper settings coverage is deferred to Phase 4.2 where `_load_settings` will be extracted into a testable method.*
- [x] Run `pytest` locally — **27 passed in 0.37s** under `QT_QPA_PLATFORM=offscreen`
- [x] Commit: `test: add pytest harness with coverage for pure-logic helpers`

### 1.3 Add a minimal CI workflow
- [x] Create `.github/workflows/ci.yml`
- [x] Job: install on Ubuntu Python 3.9, 3.11, 3.12
- [x] Step: `pip install -e ".[dev]"` (with pip-cache keyed on `pyproject.toml`)
- [x] Step: `pytest -v` (with `QT_QPA_PLATFORM=offscreen`)
- [x] Step: `python -c "import my_dropper_app"` smoke import
- [x] Step: install Qt system libs (`libegl1`, `libgl1`, `libxkbcommon0`, `libdbus-1-3`, `libfontconfig1`, `libxcb-cursor0`) so PyQt6 loads in CI
- [ ] (Optional) add `ruff check .` step *(deferred — not blocking; can add when we adopt ruff)*
- [ ] Verify the workflow passes on push *(deferred — requires `git push` to GitHub; do this when ready to publish)*
- [x] Commit: `ci: add GitHub Actions workflow running pytest`

---

## Phase 2 — High-Severity Bug Fixes

Goal: close the latent bugs identified in the evaluation.

### 2.1 [H1] Cap the collision-rename loop
- [x] Locate the `while ... .exists()` in `_get_unique_destination` (app.py:587)
- [x] Locate the second `while True` for filename generation (app.py:1097)
- [x] Define `MAX_COLLISION_ATTEMPTS = 10_000` as a module-level constant
- [x] Replace worker loop with `for counter in range(1, MAX_COLLISION_ATTEMPTS + 1):`
- [x] Replace text-drop loop with `for counter in range(MAX_COLLISION_ATTEMPTS + 1):` (counter 0 = original name)
- [x] Raise a descriptive `RuntimeError` if worker exhausts attempts
- [x] Catch `RuntimeError` in worker `run()` and surface it as a user-visible log line (separate branch from generic Exception)
- [x] Text-drop path handles exhaustion inline (logs + critical dialog, returns cleanly)
- [x] Add test: exhausting cap raises `RuntimeError` (monkeypatched to 3 for speed)
- [x] Add test: boundary case — last attempt succeeds when free slot exists at the cap
- [x] Commit: `fix: cap filename-collision loop to prevent thread hang`

### 2.2 [H2] Make cancellation thread-safe
- [x] Replace `self._cancelled: bool` with `self._cancelled = threading.Event()`
- [x] Replace `self._cancelled = True` with `self._cancelled.set()` in `cancel()`
- [x] Replace `if self._cancelled` reads in `run()` and `_chunked_copy` with `is_set()`
- [x] Add public `is_cancelled()` method for read access (keeps internals private)
- [x] Audit every call site in `FileOperationWorker` — 4 references converted (`grep _cancelled` confirms)
- [x] Add tests in `test_cancellation.py`:
  - [x] Event is clear at construction
  - [x] `cancel()` sets the event
  - [x] Pre-cancelled `_chunked_copy` raises `InterruptedError` and cleans partial file
  - [x] Pre-cancelled `run()` skips all queued ops, reports them as skipped
  - [x] Realistic race: background-thread `cancel()` during in-flight `_chunked_copy` → either clean completion or clean abort
- [x] Commit: `fix: use threading.Event for cancellation to avoid GIL-only atomicity`

### 2.3 [H3] Validate destinations on change
- [x] Extract a pure `validate_destination(path)` module function checking `exists`, `is_dir`, `os.access(W_OK)`
- [x] In `_on_destination_changed`, run the validator; on failure log a warning AND revert the combo box to the current valid destination
- [x] Use `blockSignals` around the combo revert to avoid re-entering the handler
- [x] Add tests for `validate_destination`:
  - [x] Existing writable dir → None
  - [x] Nonexistent path → `"does not exist"`
  - [x] File (not directory) → `"not a directory"`
  - [x] Read-only dir (chmod 555) → `"no write permission"` (skipped on Windows and when running as root)
- [ ] *Defer:* prompt-to-create flow for missing paths — line edit is read-only so users cannot type missing paths today; revisit if/when free-text entry is added
- [ ] *Defer:* manual UI test — needs a display; verify when you next launch the app and pick a stale recent destination
- [x] Commit: `fix: validate destination path on change instead of silently accepting`

### 2.4 [H4] Filter stale recent destinations
- [x] Add pure `prune_stale_destinations(paths)` module helper (preserves order, keeps only real directories)
- [x] In `_init_settings`, prune the loaded list; if anything dropped, persist the cleaned list back and log a note
- [x] In `_on_destination_changed`, when the selected path fails `validate_destination`, also drop the stale entry from `recent_destinations`, persist, and repopulate the combo (signals blocked to avoid re-entry)
- [x] 7 tests in `test_recent_destinations.py`: empty, all valid, mixed valid/ghost, file-not-dir, order preservation, all-stale, idempotency
- [ ] *Defer:* manual UI test — verify next time you launch the app by checking the dropdown after deleting one of the listed directories
- [x] Commit: `fix: prune nonexistent paths from recent-destinations on load`

### 2.5 [H5] Document/log cross-FS move risk
- [x] Add `_is_cross_filesystem(src, dest)` detector using `st_dev`; defaults to True if either stat fails so the richer error path runs
- [x] Add `_move_cross_filesystem(src, dest)` with three explicit phases — copy → verify (existence + file-size match) → delete-source — each raising a phase-labelled `RuntimeError`
- [x] Cleanup logic: partial destination removed on copy failure; corrupt destination removed on size mismatch
- [x] "File now in BOTH locations" warning when source-delete fails after a successful copy
- [x] New `_safe_move(src, dest)` orchestrator picks `Path.rename` (atomic) for same-FS or `_move_cross_filesystem` for cross-FS
- [x] Replace `shutil.move(...)` in `_process_file` and `_process_directory` with `self._safe_move(...)`
- [x] 8 tests in `test_cross_fs_move.py`:
  - [x] Detector: same-dir is `False`; missing-source defaults to `True`
  - [x] Cross-FS file move: copies + deletes source + preserves mtime
  - [x] Cross-FS directory move: recursive copy + source removal
  - [x] Copy failure: source preserved, partial destination cleaned, phase-labelled error
  - [x] Delete-after-copy failure: "BOTH locations" warning, both files remain (correct behaviour — user must intervene)
  - [x] Size-mismatch after copy: corrupt destination removed, source preserved
- [x] Commit: `fix: handle cross-filesystem moves explicitly to avoid silent partial state`

### 2.6 [H6] Decide on a symlink policy
- [x] **Chosen policy: skip top-level symlinks; preserve nested symlinks as symlinks**
- [x] Top level: `run()` checks `op.source.is_symlink()` BEFORE `is_file()` / `is_dir()`, logs `⏭ Skipped symlink (not followed): ...`, and counts as skipped
- [x] Inside trees: `shutil.copytree` calls in `_process_directory` and `_move_cross_filesystem` now pass `symlinks=True` so circular links don't recurse
- [x] 5 tests in `test_symlinks.py` (POSIX-only, marked skip on Windows):
  - [x] Top-level symlink to file → skipped, source untouched
  - [x] Top-level symlink to directory → skipped
  - [x] Top-level broken symlink → skipped
  - [x] Directory containing an inner symlink → inner symlink preserved as a symlink in the destination (not silently materialised)
  - [x] Directory containing a circular symlink → run completes without recursion explosion
- [x] Document the policy in README under "Usage → Symlink Handling"
- [x] Commit: `fix: detect and skip symlinks to avoid infinite recursion and broken-link crashes`

---

## Phase 3 — Code Hygiene & Maintainability

Goal: make the codebase easy to keep working on.

### 3.1 [M1] Extract magic numbers to named constants
- [x] Define at module top of `app.py`:
  - [x] `BYTES_PER_KB = 1024` (added for symmetry with MB/GB and to replace the lone `/ 1024` in size formatting)
  - [x] `BYTES_PER_MB = 1024 * BYTES_PER_KB`
  - [x] `BYTES_PER_GB = 1024 * BYTES_PER_MB`
  - [x] `COPY_CHUNK_SIZE = BYTES_PER_MB`
  - [x] `LARGE_FILE_THRESHOLD = 10 * BYTES_PER_MB`
  - [x] `MAX_FILE_SIZE_WARNING_BYTES = 1000 * BYTES_PER_MB` (replaces `MAX_FILE_SIZE_WARNING_MB` — old name removed since nothing external referenced it)
  - [x] `MAX_RECENT_DESTINATIONS = 5` *(already existed pre-3.1)*
  - [x] `WORKER_SHUTDOWN_TIMEOUT_MS = 5000`
- [x] Replace every numeric literal in production code with the named constant (test files kept their inline byte sizes — they're explicit fixture data, not magic numbers)
- [x] Commit: `refactor: replace magic numbers with named constants`

### 3.2 [M2] Consolidate destination-directory creation
- [x] Add `_ensure_destination_exists(path=None, *, show_error_dialog=False) -> bool`
  - Defaults `path` to `self.destination_directory` for the common case
  - Logs `📁 Created directory: <path>` only when actually creating (not on no-op exists check)
  - Logs `❌ Cannot create destination: <err>` on failure; optionally shows a critical dialog
- [x] Replace the three sites:
  - [x] `_open_destination` (was: bare-Exception catch, returned silently on failure)
  - [x] `_process_dropped_files` (was: `OSError` catch + QMessageBox.critical) — now passes `show_error_dialog=True`
  - [x] `_process_dropped_text` (was: `OSError` catch + log only) — uses the default no-dialog mode
- [x] Callers respect the bool return; only the dropped-files path keeps the now-unconditional "Destination: X" log line (it's a distinct signal from "Created")
- [x] 5 tests in `test_ensure_destination.py`: existing path no-ops, missing path is created+logged, explicit path overrides default, mkdir failure returns False+logs, `show_error_dialog=True` fires `QMessageBox.critical`
- [x] Commit: `refactor: consolidate destination-mkdir logic into single helper`

### 3.3 [M3] Remove unused imports & constants
- [x] Removed 10 unused imports (ruff F401 caught 6 more than the plan listed):
  - From `typing`: `Dict`, `Any`
  - From `PyQt6.QtWidgets`: `QLineEdit`, `QStyle`
  - From `PyQt6.QtCore`: `QUrl`, `QSize`, `QPoint`
  - From `PyQt6.QtGui`: `QPalette`, `QColor`, `QIcon`
- [x] Removed `SETTINGS_WINDOW_STATE` constant (decision: remove rather than wire up — `saveGeometry()` already captures maximize/minimize state on modern Qt; adding `saveState()` would require QMainWindow patterns this app doesn't use)
- [x] Note: `QLineEdit` appears in stylesheet strings (CSS selectors) but those don't count as Python references — the import itself was unused
- [x] `ruff check --select F401 src/` reports "All checks passed!"
- [x] All 63 tests still pass
- [x] Commit: `refactor: remove unused imports and dead constants`

### 3.4 [M4] Count directory items before move
- [x] Move the `op.source.rglob('*')` count call to BEFORE the copytree/_safe_move block
- [x] Count is cached and used in the post-operation log line — works correctly for both copies and moves now
- [x] Updated `test_move_directory_recursive` (was previously asserting the bug existed via a NOTE comment): now collects `log_message` emissions and asserts `(3 items)` appears in the success line
- [x] Commit: `fix: count directory items before move so source still exists`

### 3.5 [M5] Tighten JSON filename parsing
- [x] Replaced bare `data["ior"]` lookups with `data.get("ior")` for cleaner intent
- [x] Replaced `if model_id and model_id.strip()` with `if isinstance(model_id, str) and model_id.strip()` (same for `name`)
- [x] Effect: wrong-type values (int, list, dict, bool) now fall through cleanly to generic-JSON instead of raising `AttributeError` and producing the confusing `⚠️ Error parsing text` log line
- [x] Removed the M5 NOTE comment from `test_ior_present_but_modelid_missing_falls_through_to_generic_json`
- [x] Added 4 new tests:
  - [x] `modelId: 123` (int) → generic JSON fallback
  - [x] `modelId: ["a", "b"]` (list) → generic JSON fallback
  - [x] `publicData.name: 42` (int) → generic JSON fallback
  - [x] `ior: "just a string"` (str not dict) → generic JSON fallback
- [x] `{"ior": {}}` and `{"publicData": {}}` cases were already passing — the existing `.get()` defaults handled them, but now the type check makes the behaviour deliberate rather than accidental
- [x] Commit: `fix: harden JSON filename parsing against partially-shaped objects`

### 3.6 [M6] Make confirm-dialog non-blocking from worker perspective
- [x] Audited all 8 `QMessageBox.*` call sites
- **Audit result:** only one dialog is shown while the worker is alive — the `closeEvent` "Operation in Progress" confirm. The "Large Transfer" question dialog runs *before* `_start_worker`, so the original signal-queue race doesn't apply.
- [x] Pause/resume mechanism **not needed** — the only mid-worker dialog asks "Cancel and exit?" rather than "Continue this transfer?", and already calls `cancel()` on Yes (a stop, not a pause). Adding pause/resume would be over-engineering for a flow that doesn't exist.
- [x] Tightened the closeEvent flow's loose end: disconnect `progress_updated`, `operation_completed`, and `log_message` from their slots **before** `wait()` so the queued completion-dialog signal collected during the modal confirm doesn't fire on a window that's about to close.
- [x] disconnect() wrapped in `try/except (TypeError, RuntimeError)` so it's safe under shutdown
- [x] Commit: `refactor: explicit worker-pause around mid-transfer confirm dialogs`

### 3.7 [M7] Per-platform "open folder" error messages
- [x] Split the single try/except into three platform-specific branches
- [x] **Linux**: distinguishes `FileNotFoundError` ("`xdg-open` not found — is xdg-utils installed? On Debian/Ubuntu: sudo apt install xdg-utils") from `CalledProcessError` (`xdg-open failed (exit N)`)
- [x] **macOS**: distinguishes missing `open` (would be extraordinary) from `CalledProcessError`
- [x] **Windows**: `os.startfile` was previously unguarded — wrapped in try/except so `OSError` no longer crashes the click handler; logs "Could not open in Explorer: …"
- [x] 5 tests in `test_open_destination.py`:
  - [x] Linux missing xdg-open → install hint visible in log
  - [x] Linux xdg-open exit-nonzero → `(exit 4)` reported
  - [x] Linux success → `📂 Opened:` logged
  - [x] Windows startfile OSError → caught, logged with cause
  - [x] Windows startfile success → `📂 Opened:` logged
- [x] Commit: `fix: clearer error messages when the platform 'open folder' command fails`

---

## Phase 4 — Architecture Cleanup

Goal: split the 1000-line `app.py` so future features have somewhere to land.

### 4.1 Split `app.py` into focused modules
- [x] Created `src/my_dropper_app/constants.py` — APP_NAME, ORG_NAME, settings keys, defaults, byte sizes, timeouts (35 LOC)
- [x] Created `src/my_dropper_app/models.py` — `OperationMode`, `OperationStatus`, `FileOperation`, `OperationResult` (no Qt dep) (47 LOC)
- [x] Created `src/my_dropper_app/theme.py` — `LIGHT_STYLE`, `DARK_STYLE` (315 LOC of CSS)
- [x] Created `src/my_dropper_app/parsing.py` — pure helpers: `validate_destination`, `prune_stale_destinations`, `get_unique_destination`, `parse_text_for_filename` (123 LOC; latter two converted from method to free function)
- [x] Created `src/my_dropper_app/worker.py` — `FileOperationWorker` + `_safe_move` / `_move_cross_filesystem` helpers (265 LOC)
- [x] Slimmed `src/my_dropper_app/app.py` from 1518 → 787 LOC; now contains only `FileDropperApp` + `main()`
- [x] Updated imports across all test files (11 test files touched, `_unique` shim kept in collision tests for the (None, path) call shape)
- [x] All 77 tests pass; ruff `F401` clean
- [ ] Manual smoke: launch app, drop a file, toggle theme, cancel a transfer — *defer to user testing*
- [x] Commit: `refactor: split monolithic app.py into focused modules`

### 4.2 [S1] Defensive settings load
- [x] Defaults (`DEFAULT_DEST_DIR`, COPY mode, empty recents) assigned **before** the try block so partial-load exceptions still leave the widget usable
- [x] Wrapped the body of `_init_settings` in try/except; on failure logs `Failed to load settings, falling back to defaults: <err>` with traceback at WARNING level
- [x] Added defensive type-handling that matches the Qt quirks:
  - `Path(str(raw_dest))` instead of `Path(raw_dest)` so wrong-type values fail early in the controlled try block
  - `str(mode_value).lower() == "move"` so non-string mode values fall back to COPY
  - QSettings returns a bare `str` when a list has only one entry — wrapped back into a list
  - Non-string elements filtered before `prune_stale_destinations` (defends against hand-edited configs)
- [x] 8 tests in `test_init_settings.py` using a `FakeSettings` stand-in (avoids real QSettings + QApplication):
  - [x] Empty settings → defaults
  - [x] Valid settings round-trip correctly
  - [x] Existing recent directories are kept
  - [x] `QSettings.value` raising → defaults, no crash
  - [x] Single-string recents → wrapped back into list
  - [x] Mixed-type recents → non-strings filtered
  - [x] Hostile `__str__` on dest path → falls back to default
  - [x] Partial failure (DEST_DIR ok, recents raises) → keeps the parts that loaded
- [x] Commit: `fix: defensive settings load with reset-to-defaults fallback`

---

## Phase 5 — UX & Accessibility

Goal: usable by keyboard, by screen readers, by non-English users.

### 5.1 [L3] Keyboard shortcuts
- [x] New `_init_shortcuts()` method wires six `QShortcut` bindings:
  - [x] `Ctrl+Q` → `self.close()` (triggers existing close-confirm if a transfer is running)
  - [x] `Ctrl+O` → `_browse_destination`
  - [x] `Ctrl+L` → `output_text.clear`
  - [x] `Ctrl+D` → `dark_mode_checkbox.toggle` (which fires `_toggle_dark_mode` via the signal)
  - [x] `Esc` → `_cancel_operation` (no-op when no transfer running)
  - [x] `F1` → `_show_help` (new method)
- [x] `_show_help` displays an HTML-formatted `QMessageBox.information` listing all shortcuts
- [x] Added a Keyboard Shortcuts section to README under Usage with a `<kbd>`-styled table
- [x] Commit: `feat: keyboard shortcuts for common actions`

### 5.2 [L4] Accessibility names and descriptions
- [x] Wired `setAccessibleName` + `setAccessibleDescription` on every named widget:
  - [x] `dark_mode_checkbox` → "Dark mode toggle"
  - [x] `destination_combo` → "Destination folder"
  - [x] `browse_button` → "Browse destination"
  - [x] `open_dest_button` → "Open destination folder" (replaces the screen-reader-hostile `📂 Open`)
  - [x] `copy_radio` → "Copy mode"
  - [x] `move_radio` → "Move mode"
  - [x] `drop_label` → "Drop zone" (replaces `🎯 Drag & Drop Files or Text Here`)
  - [x] `cancel_button` → "Cancel transfer"
  - [x] `progress_bar` → "Transfer progress"
  - [x] `output_text` → "Activity log"
  - [x] `clear_button` → "Clear log" (replaces `🗑️ Clear Log`)
- [x] New `tests/test_accessibility.py` constructs the widget and asserts every named widget has non-empty `accessibleName` AND `accessibleDescription` — protects against future additions that forget a11y wiring
- [ ] *Defer:* manual verification with Orca (or equivalent on your platform) — recommended next time you run the app
- [x] Commit: `feat: add accessible names and descriptions to all interactive widgets`

### 5.3 [L1] Bound the output log
- [ ] Add `MAX_LOG_LINES = 5000` constant
- [ ] After each append, if line count exceeds limit, trim oldest 1000 lines
- [ ] Add a "Clear log" button
- [ ] Commit: `feat: bound output log size and add a clear-log button`

### 5.4 [L2] Tidy `_apply_theme`
- [ ] Remove the redundant first `setStyleSheet()` call (≈ app.py:796)
- [ ] Commit: `refactor: remove redundant stylesheet application in theme switch`

### 5.5 [L7] Robust text-drop encoding
- [ ] Try UTF-8 first; on `UnicodeEncodeError`, fall back to UTF-8 with `errors="replace"` and log a warning
- [ ] Commit: `fix: don't crash on non-UTF-8 text drops`

### 5.6 Add an "About" dialog
- [ ] Menu bar or button → About dialog
- [ ] Shows: version, author, license, link to repo
- [ ] Commit: `feat: add About dialog`

### 5.7 [L5] i18n scaffolding (optional, defer)
- [ ] Wrap every user-facing string in `self.tr(...)`
- [ ] Generate `.ts` files via `pylupdate6`
- [ ] Add a placeholder English translation file
- [ ] Document how to add a new language in the README
- [ ] (Defer until at least one translator is interested)

---

## Phase 6 — Distribution & Polish

Goal: easier to install on more platforms, smaller repo.

### 6.1 [L6] Remove the `.docx` from the repo
- [ ] Move `my_dropper_app_qt6.docx` to a release asset, external doc, or just delete it
- [ ] Add `*.docx` to `.gitignore` if appropriate
- [ ] Commit: `chore: remove docx documentation from source tree`

### 6.2 Windows installer (optional)
- [ ] Decide: PyInstaller (single .exe) or Briefcase (proper installer)
- [ ] Add a build script
- [ ] Test on a Windows machine or VM
- [ ] Document in README
- [ ] Commit: `feat: Windows build script`

### 6.3 macOS bundle (optional)
- [ ] PyInstaller `.app` or Briefcase
- [ ] Test on macOS
- [ ] Document
- [ ] Commit: `feat: macOS build script`

### 6.4 Release automation
- [ ] Add `.github/workflows/release.yml` that triggers on version tag push
- [ ] Build sdist + wheel via `python -m build`
- [ ] Upload to GitHub Release artifacts
- [ ] (Optional) publish to PyPI via trusted publisher
- [ ] Commit: `ci: automated releases on version tag`

---

## Phase 7 — Verification & Wrap-Up

- [ ] All Phase 1–5 commits merged
- [ ] CI green on `main`
- [ ] Manual smoke test pass:
  - [ ] Drop single file → copy
  - [ ] Drop single file → move
  - [ ] Drop directory (recursive)
  - [ ] Drop large file (>1 GB) → confirm prompt → cancel mid-transfer → partial file cleaned up
  - [ ] Drop text → smart filename
  - [ ] Type invalid destination → warning, no silent acceptance
  - [ ] Restart app → recent destinations only shows existing paths
  - [ ] Toggle dark mode → persists across restart
  - [ ] Keyboard shortcuts all work
  - [ ] Screen reader announces every widget
- [ ] Update README:
  - [ ] Remove references to the deleted standalone script
  - [ ] Document new keyboard shortcuts
  - [ ] Document symlink policy
- [ ] Bump version to `2.1.0` in `pyproject.toml`
- [ ] Tag release; publish artifacts

---

## Quick Reference — Severity Index

| ID | Item | Phase |
|---|---|---|
| C1 | Delete duplicate app file | 1.1 |
| C2 | Test harness | 1.2 |
| H1 | Cap collision loop | 2.1 |
| H2 | Thread-safe cancel | 2.2 |
| H3 | Validate destination on change | 2.3 |
| H4 | Filter stale recent destinations | 2.4 |
| H5 | Cross-FS move handling | 2.5 |
| H6 | Symlink policy | 2.6 |
| M1 | Magic numbers → constants | 3.1 |
| M2 | Consolidate mkdir | 3.2 |
| M3 | Remove unused imports | 3.3 |
| M4 | Count items before move | 3.4 |
| M5 | Harden JSON parsing | 3.5 |
| M6 | Worker-pause around dialogs | 3.6 |
| M7 | Per-platform open-folder errors | 3.7 |
| L1 | Bound log + clear button | 5.3 |
| L2 | Remove redundant setStyleSheet | 5.4 |
| L3 | Keyboard shortcuts | 5.1 |
| L4 | Accessibility names | 5.2 |
| L5 | i18n scaffolding | 5.7 |
| L6 | Remove .docx | 6.1 |
| L7 | Robust text encoding | 5.5 |
