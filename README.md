# File Dropper & Saver

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)

A modern, intuitive desktop application built with PyQt6 that allows you to drag and drop files to copy or move them to a specified directory. Perfect for quickly organizing files or creating a designated drop zone on your desktop.

## Quick Start

```bash
# Install with pipx (recommended)
pipx install git+https://github.com/hannesnortje/my_dropper_app.git

# Run the app
my-dropper-app
```

## Features

### Core Functionality
- **Drag & Drop Interface** - Simply drag files from your file manager and drop them into the application
- **Copy or Move Files** - Choose between copying or moving files to the destination
- **Directory Support** - Full recursive copy/move support for entire directories
- **Text Drop** - Drop text content to save it as a file (with smart naming for JSON)

### User Experience
- **🌙 Dark Mode** - Toggle between light and dark themes
- **Progress Tracking** - Real-time progress bar for file operations
- **Cancel Operations** - Ability to cancel long-running operations
- **Non-blocking UI** - All file operations run in background threads
- **Recent Destinations** - Quick access to recently used destinations (stale paths auto-pruned)
- **Open Destination** - One-click button to open destination folder
- **Keyboard Shortcuts** - <kbd>Ctrl</kbd>+<kbd>O</kbd>, <kbd>Esc</kbd>, <kbd>F1</kbd>, and more — full reference in-app
- **Accessibility** - Every interactive control has a screen-reader-friendly name and a hover tooltip
- **About Dialog** - Version, license, and repository link via the `ℹ️ About` button

### Smart Features
- **Automatic Renaming** - Files with duplicate names are automatically renamed
- **JSON Parsing** - Dropped JSON text extracts `modelId` or `publicData.name` for filename
- **Large File Warning** - Warns before transferring files larger than 1GB
- **Settings Persistence** - All preferences saved between sessions
- **Window Memory** - Remembers window size and position

## Installation

### Option 1: pipx (Recommended)

[pipx](https://pypa.github.io/pipx/) installs the app in an isolated environment:

```bash
# Install pipx if you don't have it
pip install pipx
pipx ensurepath

# Install from GitHub
pipx install git+https://github.com/hannesnortje/my_dropper_app.git
```

**Update:** `pipx upgrade my-dropper-app`

**Uninstall:** `pipx uninstall my-dropper-app`

### Option 2: pip

```bash
pip install git+https://github.com/hannesnortje/my_dropper_app.git
```

### Option 3: From Source

```bash
git clone https://github.com/hannesnortje/my_dropper_app.git
cd my_dropper_app
pip install -e .
```

## Usage

### Running the App

```bash
my-dropper-app    # Primary command
dropper           # Short alias
python -m my_dropper_app  # As module
```

### How to Use

1. **Set destination** - Click "Browse" to choose where dropped files should be saved
2. **Choose mode** - Select "Copy files" or "Move files"
3. **Drag and drop** - Drag files or folders into the drop zone
4. **Monitor progress** - Watch the progress bar and output log
5. **Open destination** - Click "📂 Open" to view saved files
6. **Toggle theme** - Use "🌙 Dark Mode" for a darker interface

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| <kbd>Ctrl</kbd>+<kbd>O</kbd> | Browse for destination folder |
| <kbd>Ctrl</kbd>+<kbd>L</kbd> | Clear the output log |
| <kbd>Ctrl</kbd>+<kbd>D</kbd> | Toggle dark mode |
| <kbd>Esc</kbd> | Cancel the running transfer |
| <kbd>Ctrl</kbd>+<kbd>Q</kbd> | Quit (prompts if a transfer is in progress) |
| <kbd>F1</kbd> | Show the shortcut reference dialog |

### Symlink Handling

- **Top-level symlinks are skipped, not followed.** If you drop a symbolic link directly, the app logs `⏭ Skipped symlink (not followed)` and leaves both the link and its target untouched. Drop the real path instead if you want to copy or move it.
- **Symlinks inside a dropped directory are preserved as symlinks** in the destination. This keeps recursive structures (e.g. a folder containing a link back to itself) safe and avoids silently duplicating large targets.
- **Broken symlinks are skipped** with the same message.

### Adding to Application Menu (Linux)

To add File Dropper to your application menu on Ubuntu, Kubuntu, and other Linux distributions:

#### Automatic Setup

Run this command to create the desktop entry:

```bash
# Find where the command is installed
DROPPER_PATH=$(which my-dropper-app)

# Create the desktop entry
cat > ~/.local/share/applications/my-dropper-app.desktop << EOF
[Desktop Entry]
Name=File Dropper & Saver
Comment=Drag and drop file organizer
Exec=$DROPPER_PATH
Icon=folder-download
Terminal=false
Type=Application
Categories=Utility;FileTools;
Keywords=file;drop;copy;move;organize;
EOF

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

#### Manual Setup

1. Create the file `~/.local/share/applications/my-dropper-app.desktop`:

```ini
[Desktop Entry]
Name=File Dropper & Saver
Comment=Drag and drop file organizer
Exec=/home/YOUR_USERNAME/.local/bin/my-dropper-app
Icon=folder-download
Terminal=false
Type=Application
Categories=Utility;FileTools;
Keywords=file;drop;copy;move;organize;
```

2. Replace `YOUR_USERNAME` with your actual username, or run `which my-dropper-app` to find the correct path.

3. Make it executable (optional but recommended):
```bash
chmod +x ~/.local/share/applications/my-dropper-app.desktop
```

4. Update the desktop database:
```bash
update-desktop-database ~/.local/share/applications/
```

The app should now appear in your application menu under "Utilities" or by searching for "File Dropper".

#### Using a Custom Icon

The repository ships two flavours of the icon:

| File | Best on | Notes |
|---|---|---|
| `my_dropper_icon.svg` | **Light** panels / menu bars | Black strokes; the default |
| `my_dropper_icon_light.svg` | **Dark** panels / menu bars | Off-white strokes; faint on light backgrounds |

Pick whichever matches your desktop theme:

```bash
# Copy your chosen icon to the local icons directory
mkdir -p ~/.local/share/icons

# For a LIGHT menu bar (Mint, classic GNOME, etc.):
cp /path/to/my_dropper_app/my_dropper_icon.svg ~/.local/share/icons/my-dropper-app.svg

# For a DARK menu bar (most modern GNOME / KDE Plasma):
cp /path/to/my_dropper_app/my_dropper_icon_light.svg ~/.local/share/icons/my-dropper-app.svg

# Update the desktop file to use it
sed -i 's|Icon=folder-download|Icon=my-dropper-app|' ~/.local/share/applications/my-dropper-app.desktop
```

If you change your theme later, just re-run the copy step with the other variant; the desktop entry's `Icon=my-dropper-app` reference stays the same.

#### Desktop Environments

| Desktop | Menu Location |
|---------|--------------|
| GNOME (Ubuntu) | Activities → Show Applications → search "File Dropper" |
| KDE Plasma (Kubuntu) | Application Launcher → Utilities |
| XFCE (Xubuntu) | Applications Menu → Accessories |
| Cinnamon (Mint) | Menu → Accessories |

## Configuration

Settings are stored using Qt's QSettings:

| Platform | Location |
|----------|----------|
| Linux | `~/.config/CeruleanCircle/File Dropper & Saver.conf` |
| macOS | `~/Library/Preferences/com.CeruleanCircle.File Dropper & Saver.plist` |
| Windows | Registry: `HKEY_CURRENT_USER\Software\CeruleanCircle\File Dropper & Saver` |

### Saved Settings
- Destination directory
- Recent destinations (up to 5)
- Operation mode (copy/move)
- Dark mode preference
- Window size and position

### Defaults
- **Destination:** `~/DroppedFiles_QT6`
- **Mode:** Copy
- **Theme:** Light

## Project Structure

```
my_dropper_app/
├── pyproject.toml              # Package configuration + dev extras
├── README.md
├── LICENSE                     # GPL-3.0
├── launch.sh                   # Launch script
├── my_dropper_icon.svg         # App icon
├── .github/workflows/
│   ├── ci.yml                  # Pytest on push/PR (Python 3.9/3.11/3.12)
│   └── release.yml             # Tag-triggered sdist+wheel GitHub Release
├── src/my_dropper_app/
│   ├── __init__.py             # Package init + version/author/license
│   ├── __main__.py             # python -m entry point
│   ├── app.py                  # FileDropperApp widget + main()
│   ├── constants.py            # APP_NAME, settings keys, sizes, timeouts
│   ├── models.py               # Enums + dataclasses (no Qt dep)
│   ├── parsing.py              # Pure helpers (validation, rename, parsing)
│   ├── theme.py                # Light / dark Qt stylesheets
│   └── worker.py               # FileOperationWorker (QThread)
└── tests/                      # Pytest suite (~95 tests)
```

## Development

### Setup

```bash
git clone https://github.com/hannesnortje/my_dropper_app.git
cd my_dropper_app
python -m venv .venv
source .venv/bin/activate          # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"            # includes pytest + pytest-qt
```

### Run in Development

```bash
my-dropper-app
# or
python -m my_dropper_app
```

### Run the Tests

```bash
QT_QPA_PLATFORM=offscreen pytest -v
```

The offscreen Qt platform plugin lets the suite run without a display, so
the same command works locally and in CI. There are ~95 tests covering
pure-logic helpers (filename collisions, JSON parsing, path validation,
cross-FS moves, symlink handling, cancellation, defensive settings load)
plus widget smoke tests for accessibility and keyboard shortcuts.

### Architecture

The codebase is split into focused modules so the widget code stays
focused on UI concerns and the pure logic is independently testable.

```
                    ┌───────────────────────────────┐
                    │  app.py — FileDropperApp      │
                    │  (Qt widget, drag-drop, UI)   │
                    └────┬─────────────────┬────────┘
                         │                 │
            emits drop   │                 │ starts in background
                         ▼                 ▼
                ┌──────────────┐   ┌────────────────────────┐
                │ parsing.py   │   │ worker.py              │
                │ — pure       │   │ FileOperationWorker    │
                │ helpers      │   │ (QThread)              │
                │ (validators, │   │  - chunked copy        │
                │ rename,      │   │  - cross-FS-safe move  │
                │ JSON parser, │   │  - symlink-skip policy │
                │ utf-8 save)  │   │  - threading.Event     │
                └──────┬───────┘   │    cancel              │
                       │           └─────┬──────────────────┘
                       ▼                 │
                ┌──────────────┐         │ emits signals
                │ models.py    │         │
                │ Enums +      │         ▼
                │ dataclasses  │   ┌────────────────────────┐
                └──────────────┘   │ app.py log + progress  │
                                   └────────────────────────┘

   constants.py  ←  shared by all modules (sizes, keys, timeouts)
   theme.py      ←  applied by app.py (LIGHT_STYLE / DARK_STYLE)
```

### Key Components

| Component | Module | Description |
|---|---|---|
| `FileDropperApp` | `app.py` | Main widget (QWidget); drag-drop, settings, UI assembly |
| `FileOperationWorker` | `worker.py` | QThread for background copy / move; threading.Event cancel |
| `validate_destination` | `parsing.py` | Returns reason string or None for a path |
| `prune_stale_destinations` | `parsing.py` | Filters a recent-destinations list down to existing dirs |
| `get_unique_destination` | `parsing.py` | Generates `name (N).ext` to avoid collisions (bounded loop) |
| `parse_text_for_filename` | `parsing.py` | Picks a filename + extension from dropped JSON / text |
| `save_text_utf8_with_fallback` | `parsing.py` | UTF-8 write with `errors='replace'` fallback |
| `OperationMode` / `FileOperation` / `OperationResult` | `models.py` | Plain enums + dataclasses, no Qt dependency |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| PyQt6 not found | `pip install PyQt6` |
| `xdg-open not found` on the Open button (Linux) | `sudo apt install xdg-utils` (or your distro's equivalent) |
| Permission denied on launch.sh | `chmod +x launch.sh` |
| Files not copying | Check destination permissions and disk space |
| Dark mode not applying | Toggle off/on or restart the app |
| Symlink dropped but nothing happened | Expected — see [Symlink Handling](#symlink-handling) above |

## Changelog

### v2.1.1

**UX**
- ✨ Drops that would overwrite an existing destination now show a **Replace / Keep Both / Cancel** prompt (default = Keep Both) with an "Apply to all remaining" checkbox for batch drops. Applies to both text drops (e.g. WODA `ior:local:` URLs that produce a deterministic `<uuid>.scenario.json`) and file drops.

### v2.1.0

**Reliability fixes**
- 🐛 Bounded filename-collision rename loop (couldn't hang on pathological destinations)
- 🐛 Cancellation flag is now a `threading.Event` rather than a bare bool — portable cross-thread safety, not just GIL-dependent
- 🐛 Cross-filesystem moves now explicit copy → verify → delete with phase-labelled errors (`"file now in BOTH locations"`, `"size mismatch; destination removed"`, etc.)
- 🐛 Top-level symlinks are skipped (with a clear log line); nested symlinks inside a copied tree are preserved as symlinks so circular structures stay finite
- 🐛 Stale entries in the recent-destinations dropdown are pruned at startup and after a failed pick — no more silent rejections
- 🐛 Defensive settings load: corrupt / hand-edited QSettings can no longer prevent the app from starting
- 🐛 Drag-and-drop now falls back to the text payload when dropped URLs are non-local (e.g. `ior:local:` schemes from web sources)
- 🐛 Text drops with non-UTF-8 bytes (mangled clipboards, unpaired surrogates) save with replacement chars + a warning instead of failing
- 🐛 Latent bug fixed: drag-active state on the drop zone (green border + tint) is now actually visible — was previously overwritten by `_apply_theme`

**UX & accessibility**
- ✨ Keyboard shortcuts: <kbd>Ctrl</kbd>+<kbd>O</kbd>, <kbd>Ctrl</kbd>+<kbd>L</kbd>, <kbd>Ctrl</kbd>+<kbd>D</kbd>, <kbd>Esc</kbd>, <kbd>Ctrl</kbd>+<kbd>Q</kbd>, <kbd>F1</kbd>
- ✨ <kbd>F1</kbd> opens an in-app shortcuts reference dialog
- ✨ About dialog showing version, author, license, and repository link
- ✨ Every interactive control has `accessibleName` + `accessibleDescription` for screen readers
- ✨ Every clickable control has a hover tooltip — keyboard-shortcut hints included where applicable
- ✨ Activity log bounded at 5 000 lines (Qt auto-discards oldest blocks; newest survive)
- ✨ Per-platform "open folder" error messages — Linux now tells you when `xdg-utils` is missing

**Engineering**
- 📦 Test suite added from scratch (~95 tests covering pure logic, cross-FS moves, symlinks, cancellation, settings, drop routing, a11y wiring)
- 📦 GitHub Actions CI workflow on Python 3.9, 3.11, 3.12 (`ci.yml`)
- 📦 GitHub Actions release workflow on `v*` tags — builds sdist + wheel, attaches to GitHub Release (`release.yml`)
- 🧹 Removed duplicated standalone `my_dropper_app_qt6.py` script
- 🧹 Removed 10 unused imports and a dead settings constant; ruff `F401` clean
- 🧹 Split monolithic `app.py` (1518 LOC) into focused modules — `constants`, `models`, `theme`, `parsing`, `worker`
- 🧹 Consolidated duplicated destination-mkdir logic into one helper
- 🧹 All magic numbers (chunk size, large-file threshold, GB constants, timeouts) pulled into named constants

### v2.0.0
- ✨ Background threading for file operations
- ✨ Progress bar with cancel support
- ✨ Full directory copy/move support
- ✨ Move mode (not just copy)
- ✨ Dark mode theme
- ✨ Open destination button
- ✨ Recent destinations dropdown
- ✨ Window geometry persistence
- ✨ pipx/pip installable package
- 🐛 Fixed: Directory handling now works correctly
- 🎨 Modern, polished UI

### v1.0.0
- Initial release with PyQt6
- Basic drag and drop
- Configurable destination
- Settings persistence

## License

**GNU General Public License v3.0 (GPL-3.0)**

This application uses PyQt6 (GPL-licensed). As such, this application must be distributed under a GPL-compatible license.

- ✅ Free to use, modify, and distribute
- ✅ Commercial use allowed
- ⚠️ Derivative works must be GPL-3.0
- ⚠️ Source code must be available

See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite: `QT_QPA_PLATFORM=offscreen pytest -v`
5. (Recommended) run `ruff check --select F401 src/` to catch unused imports
6. Submit a pull request — CI will re-run the suite on Python 3.9, 3.11, and 3.12

## Support

Found a bug or have a suggestion? [Open an issue](https://github.com/hannesnortje/my_dropper_app/issues).

---

Made with ❤️ using PyQt6
