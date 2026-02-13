#!/bin/bash
# Start ComfyUI-Photoshop Bridge Helper Server

echo "Starting ComfyUI-Photoshop Bridge Helper Server..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.7 or later"
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import flask" &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements_helper.txt
    echo ""
fi

# Start the server
python3 helper_server.py
