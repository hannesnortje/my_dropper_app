# Improvement Plan — File Dropper & Saver

Derived from the evaluation in `~/.claude/plans/can-you-please-thoroughly-functional-balloon.md`.
Work through phases top-to-bottom. Each phase is independently shippable.

Legend: `[C]` Critical · `[H]` High · `[M]` Medium · `[L]` Low

---

## Progress Summary

Tick the box when the entire sub-section's tasks are done. Use this as your dashboard.

**Phase 1 — Stop the Bleeding**
- [x] 1.1 [C1] Eliminate the duplicate app file
- [ ] 1.2 [C2] Stand up a test harness
- [ ] 1.3 Add a minimal CI workflow

**Phase 2 — High-Severity Bug Fixes**
- [ ] 2.1 [H1] Cap the collision-rename loop
- [ ] 2.2 [H2] Make cancellation thread-safe
- [ ] 2.3 [H3] Validate destinations on change
- [ ] 2.4 [H4] Filter stale recent destinations
- [ ] 2.5 [H5] Document/log cross-FS move risk
- [ ] 2.6 [H6] Decide on a symlink policy

**Phase 3 — Code Hygiene & Maintainability**
- [ ] 3.1 [M1] Extract magic numbers to named constants
- [ ] 3.2 [M2] Consolidate destination-directory creation
- [ ] 3.3 [M3] Remove unused imports & constants
- [ ] 3.4 [M4] Count directory items before move
- [ ] 3.5 [M5] Tighten JSON filename parsing
- [ ] 3.6 [M6] Make confirm-dialog non-blocking from worker perspective
- [ ] 3.7 [M7] Per-platform "open folder" error messages

**Phase 4 — Architecture Cleanup**
- [ ] 4.1 Split `app.py` into focused modules
- [ ] 4.2 Defensive settings load

**Phase 5 — UX & Accessibility**
- [ ] 5.1 [L3] Keyboard shortcuts
- [ ] 5.2 [L4] Accessibility names and descriptions
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
- [ ] Add `pytest` and `pytest-qt` to a new `[project.optional-dependencies]` `dev` group in `pyproject.toml`
- [ ] Create `tests/` directory with `__init__.py` and `conftest.py`
- [ ] Add `tests/test_filename_collision.py` — covers `_get_unique_destination`:
  - [ ] No collision: returns original path
  - [ ] One collision: returns `name (1).ext`
  - [ ] Sequential collisions: `(1)`, `(2)`, `(3)`
  - [ ] Extensionless files
  - [ ] Files with multiple dots (`archive.tar.gz`)
- [ ] Add `tests/test_text_parsing.py` — covers `_parse_text_for_filename`:
  - [ ] Valid JSON with `ior.modelId`
  - [ ] Valid JSON with `publicData.name`
  - [ ] Valid JSON with neither key
  - [ ] Malformed JSON (returns fallback)
  - [ ] Empty string
  - [ ] Non-JSON plain text
- [ ] Add `tests/test_file_ops.py` using `tmp_path`:
  - [ ] Copy single file
  - [ ] Move single file
  - [ ] Copy directory recursively
  - [ ] Move directory recursively
  - [ ] Copy preserves metadata (mtime)
- [ ] Add `tests/test_settings.py`:
  - [ ] Load with no prior settings → defaults
  - [ ] Load with corrupt/wrong-type values → falls back to defaults without crashing
- [ ] Run `pytest` locally — all green
- [ ] Commit: `test: add pytest harness with coverage for pure-logic helpers`

### 1.3 Add a minimal CI workflow
- [ ] Create `.github/workflows/ci.yml`
- [ ] Job: install on Ubuntu Python 3.9, 3.11, 3.12
- [ ] Step: `pip install -e ".[dev]"`
- [ ] Step: `pytest`
- [ ] Step: `python -c "import my_dropper_app"` smoke import
- [ ] (Optional) add `ruff check .` step
- [ ] Verify the workflow passes on push
- [ ] Commit: `ci: add GitHub Actions workflow running pytest`

---

## Phase 2 — High-Severity Bug Fixes

Goal: close the latent bugs identified in the evaluation.

### 2.1 [H1] Cap the collision-rename loop
- [ ] Locate the `while True` in `_get_unique_destination` (≈ app.py:583)
- [ ] Locate the second `while True` for filename generation (≈ app.py:1097)
- [ ] Define `MAX_COLLISION_ATTEMPTS = 10_000` as a module-level constant
- [ ] Replace `while True` with `for i in range(1, MAX_COLLISION_ATTEMPTS + 1):`
- [ ] Raise a descriptive `RuntimeError` if exhausted
- [ ] Catch the error in the worker and surface it as a user-visible log line
- [ ] Add test: 10 001 collisions → user sees clear error, no hang
- [ ] Commit: `fix: cap filename-collision loop to prevent thread hang`

### 2.2 [H2] Make cancellation thread-safe
- [ ] Replace `self._cancelled: bool` with `self._cancelled = threading.Event()` (or `QAtomicInt`)
- [ ] Replace assignments (`self._cancelled = True`) with `self._cancelled.set()`
- [ ] Replace reads (`if self._cancelled`) with `if self._cancelled.is_set()`
- [ ] Audit every call site in `FileOperationWorker`
- [ ] Add test: cancel mid-copy on a large temp file → worker exits, partial file removed
- [ ] Commit: `fix: use threading.Event for cancellation to avoid GIL-only atomicity`

### 2.3 [H3] Validate destinations on change
- [ ] In `_on_destination_changed` (≈ app.py:857), check `Path(text).exists()` and `os.access(path, os.W_OK)`
- [ ] If invalid: do NOT update `self.destination_directory`; show inline warning (red border or status label)
- [ ] If valid but missing: prompt user "Create this directory?" before accepting
- [ ] Test manually: type a nonsense path → warning shown, no silent acceptance
- [ ] Commit: `fix: validate destination path on change instead of silently accepting`

### 2.4 [H4] Filter stale recent destinations
- [ ] In `_load_settings`, after loading the list, filter to entries where `Path(p).exists()`
- [ ] Persist the cleaned list back so it's permanent
- [ ] On selection from dropdown, re-check existence; if gone, remove and warn
- [ ] Test manually: add a destination, delete the directory, restart app → entry is gone
- [ ] Commit: `fix: prune nonexistent paths from recent-destinations on load`

### 2.5 [H5] Document/log cross-FS move risk
- [ ] In the move branch, detect if source and destination are on different filesystems (`os.stat(...).st_dev`)
- [ ] If different: explicitly do copy-then-verify-then-delete with separate error handling
- [ ] Log clearly which phase failed if it does
- [ ] Add test using two `tmp_path` directories (best-effort — true cross-FS is hard to simulate)
- [ ] Commit: `fix: handle cross-filesystem moves explicitly to avoid silent partial state`

### 2.6 [H6] Decide on a symlink policy
- [ ] Pick a policy: **skip** (recommended) / **follow** / **ask user**
- [ ] In recursion, check `Path.is_symlink()` BEFORE `is_dir()` / `is_file()`
- [ ] If skip: log `"⏭ Skipped symlink: <path>"` and continue
- [ ] Add test: directory containing a circular symlink → no recursion explosion
- [ ] Add test: broken symlink → handled gracefully
- [ ] Document the chosen behavior in the README
- [ ] Commit: `fix: detect and skip symlinks to avoid infinite recursion and broken-link crashes`

---

## Phase 3 — Code Hygiene & Maintainability

Goal: make the codebase easy to keep working on.

### 3.1 [M1] Extract magic numbers to named constants
- [ ] Define at module top of `app.py`:
  - [ ] `BYTES_PER_MB = 1024 * 1024`
  - [ ] `COPY_CHUNK_SIZE = BYTES_PER_MB`
  - [ ] `LARGE_FILE_THRESHOLD = 10 * BYTES_PER_MB`
  - [ ] `BYTES_PER_GB = 1024 ** 3`
  - [ ] `MAX_FILE_SIZE_WARNING_BYTES = 1000 * BYTES_PER_MB` (replace `MAX_FILE_SIZE_WARNING_MB`)
  - [ ] `MAX_RECENT_DESTINATIONS = 5`
  - [ ] `WORKER_SHUTDOWN_TIMEOUT_MS = 5000`
- [ ] Replace every numeric literal with the named constant
- [ ] Commit: `refactor: replace magic numbers with named constants`

### 3.2 [M2] Consolidate destination-directory creation
- [ ] Add `_ensure_destination_exists(self) -> bool` method
- [ ] Replace the three `mkdir(parents=True, exist_ok=True)` call sites (≈ app.py:876, 967, 1085) with this helper
- [ ] Helper returns `False` and shows a user-visible error if creation fails
- [ ] Callers respect the return value
- [ ] Commit: `refactor: consolidate destination-mkdir logic into single helper`

### 3.3 [M3] Remove unused imports & constants
- [ ] Remove unused: `QLineEdit`, `QSize`, `QPoint`, `QStyle`
- [ ] Either USE `SETTINGS_WINDOW_STATE` (save window state alongside geometry) or remove it
- [ ] Run `ruff check --select F401` to verify nothing else lingers
- [ ] Commit: `refactor: remove unused imports and dead constants`

### 3.4 [M4] Count directory items before move
- [ ] Move the `op.source.rglob('*')` count call BEFORE `shutil.move(...)`
- [ ] Cache the count and use it post-operation for the success log
- [ ] Commit: `fix: count directory items before move so source still exists`

### 3.5 [M5] Tighten JSON filename parsing
- [ ] In `_parse_text_for_filename`, use `.get()` chains with defaults instead of bare `[...]` lookups
- [ ] Validate type at each step (`isinstance(v, str)` before using as filename)
- [ ] Add explicit test: `{"ior": {}}` returns the fallback, doesn't `KeyError`
- [ ] Add explicit test: `{"ior": {"modelId": 123}}` (wrong type) returns fallback
- [ ] Commit: `fix: harden JSON filename parsing against partially-shaped objects`

### 3.6 [M6] Make confirm-dialog non-blocking from worker perspective
- [ ] Audit modal dialog flows during transfer (≈ app.py:981, 1061)
- [ ] If a dialog is shown while worker is running: pause the worker explicitly (`Event.wait()`), don't rely on Qt event loop ordering
- [ ] Resume on confirm; cancel on reject
- [ ] Commit: `refactor: explicit worker-pause around mid-transfer confirm dialogs`

### 3.7 [M7] Per-platform "open folder" error messages
- [ ] Wrap each platform branch (xdg-open / open / startfile) in its own try/except
- [ ] Specific error: "Couldn't run xdg-open — is xdg-utils installed?"
- [ ] Add `os.startfile` exception handling for Windows
- [ ] Commit: `fix: clearer error messages when the platform 'open folder' command fails`

---

## Phase 4 — Architecture Cleanup

Goal: split the 1000-line `app.py` so future features have somewhere to land.

### 4.1 Split `app.py` into focused modules
- [ ] Create `src/my_dropper_app/constants.py` — all module-level constants and settings keys
- [ ] Create `src/my_dropper_app/models.py` — `OperationMode`, `OperationStatus`, `FileOperation`, `OperationResult`
- [ ] Create `src/my_dropper_app/worker.py` — `FileOperationWorker` class
- [ ] Create `src/my_dropper_app/parsing.py` — `_parse_text_for_filename`, `_get_unique_destination`, anything pure
- [ ] Create `src/my_dropper_app/theme.py` — light/dark stylesheets
- [ ] Keep `src/my_dropper_app/app.py` for the `FileDropperApp` widget + `main()`
- [ ] Update imports
- [ ] Run all tests — still green
- [ ] Manual smoke: launch app, drop a file, toggle theme, cancel a transfer
- [ ] Commit: `refactor: split monolithic app.py into focused modules`

### 4.2 [S1] Defensive settings load
- [ ] Wrap the body of `_load_settings` in try/except
- [ ] On any exception: log a warning, reset to defaults, do NOT crash
- [ ] Add test: corrupt one value type in QSettings → app still starts
- [ ] Commit: `fix: defensive settings load with reset-to-defaults fallback`

---

## Phase 5 — UX & Accessibility

Goal: usable by keyboard, by screen readers, by non-English users.

### 5.1 [L3] Keyboard shortcuts
- [ ] Add `QShortcut` for `Ctrl+Q` → quit
- [ ] Add `QShortcut` for `Ctrl+O` → open destination chooser
- [ ] Add `QShortcut` for `Ctrl+L` → clear log
- [ ] Add `QShortcut` for `Esc` → cancel running transfer (if any)
- [ ] Add `QShortcut` for `Ctrl+D` → toggle dark mode
- [ ] Document shortcuts in README and in a new in-app "Help" dialog
- [ ] Commit: `feat: keyboard shortcuts for common actions`

### 5.2 [L4] Accessibility names and descriptions
- [ ] For every `QPushButton`, `QComboBox`, `QCheckBox`, `QTextEdit`, `QProgressBar`:
  - [ ] `setAccessibleName(...)` with the action ("Toggle dark mode", "Open destination folder", etc.)
  - [ ] `setAccessibleDescription(...)` with one sentence of context
- [ ] Verify with Orca screen reader (or platform equivalent): every interactive widget announces something meaningful
- [ ] Commit: `feat: add accessible names and descriptions to all interactive widgets`

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
