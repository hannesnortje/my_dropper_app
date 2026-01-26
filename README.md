# File Dropper & Saver (PyQt6)

A modern, intuitive desktop application built with PyQt6 that allows you to drag and drop files to copy or move them to a specified directory. Perfect for quickly organizing files or creating a designated drop zone on your desktop.

## Features

### Core Functionality
- **Drag & Drop Interface**: Simply drag files from your file manager and drop them into the application window
- **Copy or Move Files**: Choose between copying or moving files to the destination
- **Directory Support**: Full recursive copy/move support for entire directories
- **Text Drop**: Drop text content to save it as a file (with smart naming for JSON)

### User Experience
- **🌙 Dark Mode**: Toggle between light and dark themes
- **Progress Tracking**: Real-time progress bar for file operations
- **Cancel Operations**: Ability to cancel long-running operations
- **Non-blocking UI**: All file operations run in background threads
- **Recent Destinations**: Quick access to recently used destinations
- **Open Destination**: One-click button to open destination folder

### Smart Features
- **Automatic Renaming**: Files with duplicate names are automatically renamed
- **JSON Parsing**: Dropped JSON text extracts `modelId` or `publicData.name` for filename
- **Large File Warning**: Warns before transferring files larger than 1GB
- **Settings Persistence**: All preferences saved between sessions
- **Window Memory**: Remembers window size and position

### Technical
- **Thread-safe Operations**: Uses QThread for background file operations
- **Cross-platform**: Works on Linux, Windows, and macOS
- **Type Hints**: Full Python type annotations
- **Logging**: Comprehensive logging for debugging

## Screenshots

![App Icon](my_dropper_icon.svg)

## Requirements

- Python 3.9 or higher
- PyQt6
- Linux/Windows/macOS

## Installation

### Option 1: Install with pipx (Recommended)

The easiest way to install is using [pipx](https://pypa.github.io/pipx/), which installs the app in an isolated environment:

```bash
# Install pipx if you don't have it
pip install pipx
pipx ensurepath

# Install directly from GitHub
pipx install git+https://github.com/hannesnortje/my_dropper_app.git

# Run the app
my-dropper-app
# or
dropper
```

To update to the latest version:
```bash
pipx upgrade my-dropper-app
```

To uninstall:
```bash
pipx uninstall my-dropper-app
```

### Option 2: Install with pip

```bash
# Install from GitHub
pip install git+https://github.com/hannesnortje/my_dropper_app.git

# Run the app
my-dropper-app
```

### Option 3: Development Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/hannesnortje/my_dropper_app.git
   cd my_dropper_app
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Linux/macOS
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. Install in development mode:
   ```bash
   pip install -e .
   ```

4. Run the app:
   ```bash
   my-dropper-app
   # or
   python -m my_dropper_app
   ```

## Usage

### Running the Application

After installation, you can run the app using any of these commands:

```bash
# Primary command
my-dropper-app

# Short alias
dropper

# As a Python module
python -m my_dropper_app
```

### How to Use

1. **Launch the application** using one of the methods above
2. **Set destination directory**: Click "Browse" to choose where dropped files should be saved
3. **Choose operation mode**: Select "Copy files" or "Move files"
4. **Drag and drop**: Drag any files or folders from your file manager into the drop zone
5. **Monitor progress**: Watch the progress bar and output log for real-time feedback
6. **Open destination**: Click the "📂 Open" button to view saved files
7. **Toggle dark mode**: Use the "🌙 Dark Mode" checkbox for a darker interface

### Keyboard Shortcuts

- All interactions are mouse-based for simplicity

## Configuration

The application stores its settings using Qt's QSettings:
- **Linux**: `~/.config/CeruleanCircle/File Dropper & Saver.conf`
- **macOS**: `~/Library/Preferences/com.CeruleanCircle.File Dropper & Saver.plist`
- **Windows**: Registry under `HKEY_CURRENT_USER\Software\CeruleanCircle\File Dropper & Saver`

### Saved Settings

- Destination directory
- Recent destinations (up to 5)
- Operation mode (copy/move)
- Dark mode preference
- Window size and position

### Default Settings

- **Default destination directory**: `~/DroppedFiles_QT6`
- **Default operation mode**: Copy
- **Default theme**: Light mode

## File Structure

```
my_dropper_app/
├── pyproject.toml              # Package configuration
├── README.md                   # This file
├── LICENSE                     # GPL-3.0 license
├── requirements.txt            # Python dependencies (legacy)
├── my_dropper_app_qt6.py       # Standalone script (legacy)
├── launch.sh                   # Launch script for Linux/macOS
├── my_dropper_icon.svg         # Application icon
└── src/
    └── my_dropper_app/
        ├── __init__.py         # Package init with version
        ├── __main__.py         # Entry point for python -m
        └── app.py              # Main application code
```

## Development

### Setting up Development Environment

1. Clone and install in development mode:
   ```bash
   git clone https://github.com/hannesnortje/my_dropper_app.git
   cd my_dropper_app
   pip install -e .
   ```

2. Make your changes to `src/my_dropper_app/app.py`

3. Test the application:
   ```bash
   python3 my_dropper_app_qt6.py
   ```

### Key Components

- **FileDropperApp**: Main application class inheriting from QWidget
- **FileOperationWorker**: QThread subclass for background file operations
- **OperationMode**: Enum for copy/move operations
- **FileOperation**: Dataclass representing a single file operation
- **OperationResult**: Dataclass for operation results

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

## Troubleshooting

### Common Issues

1. **PyQt6 not found**:
   ```bash
   pip install PyQt6
   ```

2. **Permission denied on launch.sh**:
   ```bash
   chmod +x launch.sh
   ```

3. **Virtual environment not activating**:
   - Ensure you're in the correct directory
   - Check that `.venv/bin/activate` exists
   - Recreate the virtual environment if necessary

4. **Files not copying/moving**:
   - Check destination directory permissions
   - Ensure sufficient disk space
   - Verify source file accessibility
   - Check the output log for detailed error messages

5. **UI freezing** (should not happen in v2.0+):
   - This version uses background threads for all file operations
   - If issues persist, please report a bug

6. **Dark mode not applying correctly**:
   - Toggle dark mode off and on again
   - Restart the application

## Changelog

### Version 2.0.0 (Current)
- ✨ **Threading**: All file operations now run in background threads
- ✨ **Progress Bar**: Real-time progress tracking with cancel support
- ✨ **Directory Support**: Full recursive copy/move for directories
- ✨ **Move Mode**: New option to move files instead of just copying
- ✨ **Dark Mode**: Beautiful dark theme option
- ✨ **Open Destination**: Quick button to open destination folder
- ✨ **Recent Destinations**: Dropdown with recently used destinations
- ✨ **Window Memory**: Saves and restores window size/position
- ✨ **Type Hints**: Full Python type annotations
- ✨ **Logging**: Proper logging framework
- ✨ **Large File Warning**: Warns before large transfers
- 🐛 **Fixed**: Directory handling now actually copies directories
- 🎨 **UI**: Modern, polished interface with better visual feedback

### Version 1.0.0
- Initial release with PyQt6
- Basic drag and drop functionality
- Configurable destination directory
- Settings persistence
- Real-time output feedback

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is released under the **GNU General Public License v3.0 (GPL-3.0)**.

**Important**: This application uses PyQt6, which is dual-licensed under commercial and GPL licenses. Since we are using the free version of PyQt6, this application must be distributed under a GPL-compatible license. The GPL-3.0 license ensures compliance with PyQt6's licensing requirements.

### What this means:
- ✅ You can use, modify, and distribute this software freely
- ✅ You can use it for personal and commercial purposes
- ⚠️ If you distribute modified versions, they must also be open source under GPL-3.0
- ⚠️ Any software that incorporates this code must also be GPL-compatible

See the [LICENSE](LICENSE) file for the complete license text.

## Support

If you encounter any issues or have suggestions for improvements, please create an issue in the repository or contact the maintainer.

---

Made with ❤️ using PyQt6
