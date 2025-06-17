#!/bin/bash

# Define the path to your application's directory
APP_DIR="/home/hannesn/my_dropper_app" # <--- IMPORTANT: Ensure this is your actual path

# Change to the application directory
cd "$APP_DIR" || { echo "Error: Could not change to application directory."; exit 1; }

# Activate the virtual environment
source venv/bin/activate || { echo "Error: Could not activate virtual environment."; exit 1; }

# Run the Python application
python my_dropper_app_qt6.py

# Deactivate the virtual environment (optional, but good practice if you want to clean up)
# This won't affect the running GUI app, but will deactivate the shell environment
# from which the app was launched. If you're running this from a terminal,
# it will deactivate the terminal's venv once the app is closed.
# For a .desktop file, this line isn't strictly necessary as the shell process
# for the Exec command exits anyway.
# deactivate
