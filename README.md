# File Dropper & Saver (PyQt6)

A simple and intuitive desktop application built with PyQt6 that allows you to drag and drop files to save them to a specified directory. Perfect for quickly organizing files or creating a designated drop zone on your desktop.

## Features

- **Drag & Drop Interface**: Simply drag files from your file manager and drop them into the application window
- **Configurable Destination**: Set your preferred destination directory for dropped files
- **File Management**: Copy or move files to the destination folder
- **Settings Persistence**: Your preferred settings are saved and restored between sessions
- **Real-time Feedback**: Live output showing the status of file operations
- **Cross-platform**: Works on Linux, Windows, and macOS

## Screenshots

![App Icon](my_dropper_icon.svg)

## Requirements

- Python 3.6 or higher
- PyQt6
- Linux/Windows/macOS

## Installation

### Option 1: Using Virtual Environment (Recommended)

1. Clone or download this repository:
   ```bash
   git clone <repository-url>
   cd my_dropper_app
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Linux/macOS
   # or
   venv\Scripts\activate     # On Windows
   ```

4. Install PyQt6:
   ```bash
   pip install PyQt6
   ```

### Option 2: System-wide Installation

Install PyQt6 directly on your system:
```bash
pip install PyQt6
```

## Usage

### Running the Application

#### Using the Launch Script (Linux/macOS)

1. Make sure the launch script is executable:
   ```bash
   chmod +x launch.sh
   ```

2. Update the `APP_DIR` path in `launch.sh` to match your installation directory

3. Run the application:
   ```bash
   ./launch.sh
   ```

#### Direct Python Execution

```bash
python3 my_dropper_app_qt6.py
```

### How to Use

1. **Launch the application** using one of the methods above
2. **Set destination directory** (optional): Click "Browse" to choose where dropped files should be saved
3. **Drag and drop files**: Drag any files from your file manager into the application window
4. **Monitor progress**: Watch the output area for real-time feedback on file operations
5. **Settings are automatically saved** for future sessions

## Configuration

The application stores its settings in:
- Linux/macOS: `~/.config/my_dropper_app_settings.json`
- Windows: Similar location in user config directory

### Default Settings

- **Default destination directory**: `~/DroppedFiles_QT6`
- Settings are automatically created on first run

## File Structure

```
my_dropper_app/
├── my_dropper_app_qt6.py    # Main application file
├── launch.sh                # Launch script for Linux/macOS
├── my_dropper_icon.svg      # Application icon
├── my_dropper_app_qt6.docx  # Documentation (if applicable)
├── README.md                # This file
├── .gitignore              # Git ignore rules
└── venv/                   # Virtual environment (if created)
```

## Development

### Setting up Development Environment

1. Follow the installation steps above
2. Make your changes to `my_dropper_app_qt6.py`
3. Test the application:
   ```bash
   python3 my_dropper_app_qt6.py
   ```

### Key Components

- **FileDropperApp**: Main application class inheriting from QWidget
- **Drag & Drop Handling**: Implemented through `dragEnterEvent` and `dropEvent` methods
- **Settings Management**: JSON-based configuration storage
- **Signal/Slot System**: Used for thread-safe UI updates

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
   - Check that `venv/bin/activate` exists
   - Recreate the virtual environment if necessary

4. **Files not copying/moving**:
   - Check destination directory permissions
   - Ensure sufficient disk space
   - Verify source file accessibility

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

## Open Source Notice

This project is open source and distributed under the GNU General Public License v3.0 (GPL-3.0). By using PyQt6, which is licensed under GPL/commercial terms, this application and any modifications or distributions must also comply with the GPL-3.0 license. You are free to use, modify, and distribute this software, provided that any derivative works are also open source under the same license.

See the [LICENSE](LICENSE) file for details.

## Changelog

### Current Version
- Initial release with PyQt6
- Drag and drop functionality
- Configurable destination directory
- Settings persistence
- Real-time output feedback

## Support

If you encounter any issues or have suggestions for improvements, please create an issue in the repository or contact the maintainer.
