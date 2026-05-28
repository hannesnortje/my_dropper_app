#!/bin/bash

# File Dropper & Saver - Launch Script
# This script provides multiple ways to run the application

# Try to run the installed command first
if command -v my-dropper-app &> /dev/null; then
    my-dropper-app "$@"
    exit $?
fi

# Try the short alias
if command -v dropper &> /dev/null; then
    dropper "$@"
    exit $?
fi

# Fallback: Run from source
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for virtual environment in the script directory
if [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Try running as a module (works when installed in dev mode or from a venv)
python -m my_dropper_app "$@" && exit 0

echo "Error: Could not find a way to run the application."
echo "Please install with: pip install -e . or pipx install git+https://github.com/hannesnortje/my_dropper_app.git"
exit 1
