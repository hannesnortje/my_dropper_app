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
- **Recent Destinations** - Quick access to recently used destinations
- **Open Destination** - One-click button to open destination folder

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

If you cloned the repository, you can use the included icon:

```bash
# Copy icon to local icons directory
mkdir -p ~/.local/share/icons
cp /path/to/my_dropper_app/my_dropper_icon.svg ~/.local/share/icons/my-dropper-app.svg

# Update the desktop file to use it
sed -i 's|Icon=folder-download|Icon=my-dropper-app|' ~/.local/share/applications/my-dropper-app.desktop
```

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
├── pyproject.toml              # Package configuration
├── README.md
├── LICENSE                     # GPL-3.0
├── launch.sh                   # Launch script
├── my_dropper_icon.svg         # App icon
└── src/my_dropper_app/
    ├── __init__.py             # Package init
    ├── __main__.py             # python -m entry point
    └── app.py                  # Main application
```

## Development

### Setup

```bash
git clone https://github.com/hannesnortje/my_dropper_app.git
cd my_dropper_app
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .
```

### Run in Development

```bash
my-dropper-app
# or
python -m my_dropper_app
```

### Architecture

```
┌─────────────────────────────────────────────────┐
│              FileDropperApp (Main UI)           │
├─────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌────────────────────────┐   │
│  │  Settings   │  │     Drop Zone          │   │
│  │  (QSettings)│  │  (Drag & Drop Events)  │   │
│  └─────────────┘  └────────────────────────┘   │
│                          │                      │
│                          ▼                      │
│  ┌──────────────────────────────────────────┐  │
│  │      FileOperationWorker (QThread)       │  │
│  │  - Runs in background                    │  │
│  │  - Emits progress signals                │  │
│  │  - Supports cancellation                 │  │
│  └──────────────────────────────────────────┘  │
│                          │                      │
│                          ▼                      │
│  ┌──────────────────────────────────────────┐  │
│  │         Progress UI & Output Log         │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Key Components

| Component | Description |
|-----------|-------------|
| `FileDropperApp` | Main application class (QWidget) |
| `FileOperationWorker` | QThread for background file operations |
| `OperationMode` | Enum for copy/move operations |
| `FileOperation` | Dataclass for a single file operation |
| `OperationResult` | Dataclass for operation results |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| PyQt6 not found | `pip install PyQt6` |
| Permission denied on launch.sh | `chmod +x launch.sh` |
| Files not copying | Check destination permissions and disk space |
| Dark mode not applying | Toggle off/on or restart the app |

## Changelog

### v2.0.0 (Current)
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
4. Test thoroughly
5. Submit a pull request

## Support

Found a bug or have a suggestion? [Open an issue](https://github.com/hannesnortje/my_dropper_app/issues).

---

Made with ❤️ using PyQt6
