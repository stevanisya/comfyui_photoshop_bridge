@echo off
REM Start ComfyUI-Photoshop Bridge Helper Server

echo Starting ComfyUI-Photoshop Bridge Helper Server...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.7 or later from https://www.python.org/
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements_helper.txt
    echo.
)

REM Start the server
python helper_server.py
pause
