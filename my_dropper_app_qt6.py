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
import sys
import os
import shutil
import json

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox,
    QFileDialog, QLineEdit, QHBoxLayout
)
from PyQt6.QtCore import (
    Qt, QUrl, QEvent, pyqtSignal
)
from PyQt6.QtGui import (
    QDragEnterEvent, QDropEvent
)

# --- Configuration & Settings ---
SETTINGS_FILE = os.path.expanduser("~/.config/my_dropper_app_settings.json")
DEFAULT_DEST_DIR = os.path.expanduser("~/DroppedFiles_QT6")

class FileDropperApp(QWidget):
    update_output_signal = pyqtSignal(str)
    # Changed signal to pass title and message as strings
    show_message_signal = pyqtSignal(str, str) # No longer passing parent via signal

    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Dropper & Saver (PyQt6)")
        self.setGeometry(100, 100, 700, 500)

        self.setAcceptDrops(True)

        self.destination_directory = DEFAULT_DEST_DIR
        self.load_settings()

        self.init_ui()
        self.update_output_signal.connect(self.output_text_edit.append)
        # FIX: Connect the signal to a lambda that correctly calls QMessageBox.information
        self.show_message_signal.connect(lambda title, msg: QMessageBox.information(self, title, msg))


    def load_settings(self):
        """Loads application settings from a JSON file."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    self.destination_directory = settings.get('destination_directory', DEFAULT_DEST_DIR)
                    print(f"Loaded destination: {self.destination_directory}")
            except json.JSONDecodeError as e:
                print(f"Error loading settings file: {e}")
                self.destination_directory = DEFAULT_DEST_DIR
        else:
            print("Settings file not found, using default destination.")


    def save_settings(self):
        """Saves current application settings to a JSON file."""
        settings = {'destination_directory': self.destination_directory}
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            print(f"Settings saved to: {SETTINGS_FILE}")
        except IOError as e:
            print(f"Error saving settings: {e}")

    def init_ui(self):
        main_layout = QVBoxLayout()

        settings_layout = QHBoxLayout()
        settings_label = QLabel("Destination:")
        self.destination_line_edit = QLineEdit(self.destination_directory)
        self.destination_line_edit.setReadOnly(True)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_destination)

        settings_layout.addWidget(settings_label)
        settings_layout.addWidget(self.destination_line_edit)
        settings_layout.addWidget(browse_button)
        main_layout.addLayout(settings_layout)

        self.drop_label = QLabel("Drag & Drop Files/Text Here")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet(
            "QLabel { "
            "   border: 3px dashed #7a7a7a; "
            "   background-color: #f0f0f0; "
            "   padding: 20px; "
            "   font-size: 18px; "
            "   color: #333; "
            "}"
        )
        main_layout.addWidget(self.drop_label)

        self.output_text_edit = QTextEdit()
        self.output_text_edit.setPlaceholderText("Dropped items and processing logs will appear here...")
        self.output_text_edit.setReadOnly(True)
        main_layout.addWidget(self.output_text_edit)

        self.clear_button = QPushButton("Clear Output")
        self.clear_button.clicked.connect(self.output_text_edit.clear)
        main_layout.addWidget(self.clear_button)

        self.setLayout(main_layout)

    def browse_destination(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Select Destination Directory", self.destination_directory)
        if new_dir:
            self.destination_directory = new_dir
            self.destination_line_edit.setText(new_dir)
            self.save_settings()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
            self.drop_label.setStyleSheet(
                "QLabel { "
                "   border: 3px dashed #3a7a3a; "
                "   background-color: #e0ffe0; "
                "   padding: 20px; "
                "   font-size: 18px; "
                "   color: #333; "
                "}"
            )
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QEvent):
        self.drop_label.setStyleSheet(
            "QLabel { "
            "   border: 3px dashed #7a7a7a; "
            "   background-color: #f0f0f0; "
            "   padding: 20px; "
            "   font-size: 18px; "
            "   color: #333; "
            "}"
        )
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self.drop_label.setStyleSheet(
            "QLabel { "
            "   border: 3px dashed #7a7a7a; "
            "   background-color: #f0f0f0; "
            "   padding: 20px; "
            "   font-size: 18px; "
            "   color: #333; "
            "}"
        )

        self.update_output_signal.emit("\n--- New Drop Event ---")

        if event.mimeData().hasUrls():
            dropped_file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    dropped_file_paths.append(url.toLocalFile())
                else:
                    self.update_output_signal.emit(f"Skipping non-local URL: {url.toString()}")
            if dropped_file_paths:
                self.process_dropped_files(dropped_file_paths)
        elif event.mimeData().hasText():
            self.process_dropped_text(event.mimeData().text())
        else:
            self.update_output_signal.emit("Dropped data format not supported.")
            event.ignore()
            return

        event.acceptProposedAction()

    def process_dropped_files(self, file_paths):
        self.update_output_signal.emit(f"Received {len(file_paths)} file(s):")

        try:
            os.makedirs(self.destination_directory, exist_ok=True)
            self.update_output_signal.emit(f"Saving to: {self.destination_directory}")
        except OSError as e:
            error_msg = f"Error creating destination directory '{self.destination_directory}': {e}"
            self.update_output_signal.emit(error_msg)
            self.show_message_signal.emit("Error", error_msg)
            return

        success_count = 0
        fail_count = 0
        for path in file_paths:
            base_name = os.path.basename(path)
            self.update_output_signal.emit(f"  Processing: '{base_name}'")
            dest_path = os.path.join(self.destination_directory, base_name)

            try:
                if os.path.isfile(path):
                    if os.path.exists(dest_path):
                        name, ext = os.path.splitext(base_name)
                        i = 1
                        while os.path.exists(dest_path):
                            dest_path = os.path.join(self.destination_directory, f"{name} ({i}){ext}")
                            i += 1
                        shutil.copy(path, dest_path)
                        self.update_output_signal.emit(f"    Copied (renamed) to '{os.path.basename(dest_path)}'.")
                        success_count += 1
                    else:
                        shutil.copy(path, dest_path)
                        self.update_output_signal.emit(f"    Copied '{base_name}'.")
                        success_count += 1

                elif os.path.isdir(path):
                    self.update_output_signal.emit(f"    Directory '{base_name}' handled (consider recursive copy if needed).")
                    success_count += 1
                else:
                    self.update_output_signal.emit(f"    Unsupported item type (not file/directory): '{base_name}'")
                    fail_count += 1

            except PermissionError as e:
                self.update_output_signal.emit(f"    Permission Denied for '{base_name}': {e}")
                fail_count += 1
            except FileNotFoundError as e:
                self.update_output_signal.emit(f"    File Not Found for '{base_name}': {e}")
                fail_count += 1
            except shutil.Error as e:
                self.update_output_signal.emit(f"    File operation error for '{base_name}': {e}")
                fail_count += 1
            except Exception as e:
                self.update_output_signal.emit(f"    An unexpected error occurred for '{base_name}': {e}")
                fail_count += 1

        summary_message = (f"Finished processing. Successfully handled {success_count} item(s), "
                           f"{fail_count} failed.")
        self.update_output_signal.emit(summary_message)
        self.show_message_signal.emit("Drop Operation Complete", summary_message)

    def process_dropped_text(self, text_data):
        self.update_output_signal.emit(f"Received dropped text data ({len(text_data)} characters).")

        try:
            os.makedirs(self.destination_directory, exist_ok=True)
            self.update_output_signal.emit(f"Saving text to: {self.destination_directory}")
        except OSError as e:
            error_msg = f"Error creating destination directory '{self.destination_directory}': {e}"
            self.update_output_signal.emit(error_msg)
            self.show_message_signal.emit("Error", error_msg)
            return

        # Try to parse JSON and extract modelId from ior.modelId
        filename_base = "dropped_text"
        file_extension = "json"
        try:
            data = json.loads(text_data)
            if isinstance(data, dict) and "ior" in data and "modelId" in data["ior"]:
                model_id = data["ior"]["modelId"]
                if model_id and model_id.strip():
                    filename_base = f"{model_id}.scenario"
                    file_extension = "json"
                    self.update_output_signal.emit(f"Using modelId: '{model_id}' for filename")
                else:
                    self.update_output_signal.emit("Found ior.modelId but it's empty, using default name")
            elif isinstance(data, dict) and "publicData" in data and "name" in data["publicData"]:
                extracted_name = data["publicData"]["name"]
                if extracted_name and extracted_name.strip():
                    # Sanitize filename (remove invalid characters)
                    filename_base = "".join(c for c in extracted_name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                    if not filename_base:  # fallback if sanitization removes everything
                        filename_base = "dropped_text"
                    file_extension = "ior"
                    self.update_output_signal.emit(f"Using extracted name: '{filename_base}'")
                else:
                    self.update_output_signal.emit("Found publicData.name but it's empty, using default name")
                    file_extension = "ior"
            else:
                self.update_output_signal.emit("No ior.modelId or publicData.name found in JSON, using default name")
                file_extension = "ior"
        except json.JSONDecodeError:
            self.update_output_signal.emit("Text is not valid JSON, using default name")
            file_extension = "txt"
        except Exception as e:
            self.update_output_signal.emit(f"Error parsing JSON: {e}, using default name")
            file_extension = "ior"

        # Generate unique filename
        i = 0
        while True:
            if i == 0:
                filename = f"{filename_base}.{file_extension}"
            else:
                filename = f"{filename_base}_{i:03d}.{file_extension}"
            file_path = os.path.join(self.destination_directory, filename)
            if not os.path.exists(file_path):
                break
            i += 1

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_data)
            self.update_output_signal.emit(f"  Saved text to: '{filename}'")
            self.show_message_signal.emit("Text Saved", f"Successfully saved dropped text to:\n'{filename}'")
        except Exception as e:
            error_msg = f"Error saving text data: {e}"
            self.update_output_signal.emit(error_msg)
            self.show_message_signal.emit("Error", error_msg)

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileDropperApp()
    window.show()
    sys.exit(app.exec())
