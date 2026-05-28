"""Light and dark Qt stylesheets.

These are plain strings; the FileDropperApp picks one and applies it via
setStyleSheet(). Kept out of app.py so the 300+ lines of CSS don't drown
the rest of the widget logic.
"""

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
