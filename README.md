# ComfyUI-Photoshop Bridge

> ⚠️ **Work in Progress** - This project is under active development. Some features may not work as expected yet. Currently testing and fixing export functionality.

A bridge to seamlessly transfer images between Adobe Photoshop and ComfyUI using a local helper server.

## Features

- **Photoshop → ComfyUI**: Export layers or full document directly to ComfyUI
- **Works with RunPod**: Supports remote ComfyUI instances via helper server
- **ComfyUI Nodes**: Custom nodes to load latest Photoshop exports automatically
- **ComfyUI → Photoshop**: Send generated images back to Photoshop as new layers *(coming soon)*

## Project Structure

```
comfyui_photoshop_bridge/
├── __init__.py                   # ComfyUI node loader
├── photoshop_bridge_nodes.py     # Custom node implementations
├── helper_server.py              # Local helper server (NEW)
├── requirements.txt              # ComfyUI node dependencies
├── requirements_helper.txt       # Helper server dependencies (NEW)
├── photoshop_plugin/             # Photoshop UXP plugin
│   ├── manifest.json
│   ├── index_helper.html         # Plugin UI (NEW)
│   ├── index_runpod.html         # Old version (deprecated)
│   └── README.md
└── README.md
```

## How It Works

The bridge uses a **helper server** to solve UXP plugin file system limitations:

1. **Photoshop Plugin** (your computer) exports image and sends to helper server
2. **Helper Server** (your computer, localhost:8765) forwards to ComfyUI
3. **ComfyUI** (RunPod or local) receives and stores the image
4. **ComfyUI Nodes** automatically detect and load the latest uploaded image

### Architecture for Photoshop (Local) + ComfyUI (RunPod)

```
┌─────────────────────────────────┐        ┌──────────────────────┐
│      YOUR COMPUTER              │        │      RUNPOD SERVER   │
│                                 │        │                      │
│  ┌───────────────────────┐     │        │  ┌────────────────┐  │
│  │   Photoshop Plugin    │     │        │  │    ComfyUI     │  │
│  └──────────┬────────────┘     │        │  │   + Nodes      │  │
│             │                   │        │  └───────▲────────┘  │
│             ▼                   │        │          │           │
│  ┌───────────────────────┐     │        │          │           │
│  │   Helper Server       │     │  HTTPS │          │           │
│  │  (localhost:8765)     │─────┼────────┼──────────┘           │
│  └───────────────────────┘     │Internet│                      │
│                                 │        │                      │
└─────────────────────────────────┘        └──────────────────────┘
```

**Important:** The helper server runs **on your local computer** (same machine as Photoshop), not on RunPod. It acts as a bridge to forward images from Photoshop to your remote ComfyUI instance.

## Quick Start

**macOS/Linux:**
```bash
cd comfyui_photoshop_bridge
./start_helper.sh
```

**Windows:**
```
Double-click start_helper.bat
```

Then follow the [Installation](#installation) and [Usage](#usage) sections below.

## Installation

### 1. Helper Server (Local Machine)

The helper server runs on your local machine and bridges between Photoshop and ComfyUI:

```bash
# Clone the repository
git clone https://github.com/stevanisya/comfyui_photoshop_bridge.git
cd comfyui_photoshop_bridge

# Install Python dependencies for helper server
pip install -r requirements_helper.txt

# Start the helper server
python helper_server.py
```

The server will run on `http://localhost:8765`. Keep it running while using the bridge.

### 2. ComfyUI Nodes (RunPod / Server)

SSH into your ComfyUI instance and install the custom nodes:

```bash
# Navigate to ComfyUI custom_nodes folder
cd /workspace/ComfyUI/custom_nodes

# Clone the repository
git clone https://github.com/stevanisya/comfyui_photoshop_bridge.git

# Install Python dependencies (optional - uses standard ComfyUI dependencies)
cd comfyui_photoshop_bridge
pip install -r requirements.txt

# Restart ComfyUI
cd /workspace/ComfyUI
python main.py
```

### 3. Photoshop Plugin (Local Machine)

1. Install **UXP Developer Tool**:
   - Open Adobe Creative Cloud app
   - Go to "All Apps"
   - Search for "UXP Developer Tools" and install

2. Load the plugin:
   - Open UXP Developer Tool
   - Click "Add Plugin"
   - Select the `photoshop_plugin` folder from this repo
   - Click "Load" and select your Photoshop version

3. In Photoshop:
   - Go to **Plugins → ComfyUI Bridge**
   - The plugin panel will appear

4. **Important**: Enable required settings in Photoshop:
   - Go to **Preferences → Plugins**
   - Check **"Enable Developer Mode"**
   - Check **"Enable Generator"**
   - Restart Photoshop

## Usage

### 1. Start the Helper Server

Before using the plugin, start the helper server on your local machine:

```bash
cd comfyui_photoshop_bridge
python helper_server.py
```

You should see:
```
ComfyUI-Photoshop Bridge Helper Server
Starting server on http://localhost:8765
```

**Keep this terminal window open** while using the bridge.

### 2. Configure Connection

In the Photoshop plugin panel:

1. Click **"Test Helper Connection"** to verify helper server is running
   - ✓ Should show "Helper server is running!"

2. Enter your ComfyUI URL:
   - **For RunPod**: `https://xxxxx-8188.proxy.runpod.net`
   - **For Local ComfyUI**: `http://localhost:8188`

3. Click **"Test ComfyUI Connection"** to verify
   - ✓ Should show "Connected to ComfyUI via helper!"

### 3. Send Images from Photoshop to ComfyUI

1. Open an image in Photoshop
2. Choose export type:
   - **Active Layer**: Exports only the selected layer
   - **Full Document**: Exports the entire flattened image
3. Click **"Send to ComfyUI"**
4. **Choose where to save the temporary export** (any location is fine - the file will be auto-deleted after upload)
5. Progress: 📁 File picker → ⏳ Exporting → ⏳ Uploading → ✓ Uploaded!
6. The image is now in ComfyUI's input folder

### 4. Load in ComfyUI

In your ComfyUI workflow:

1. Add the **"Load Image from Photoshop"** node (category: UnaCustom)
2. Toggle the **refresh checkbox** to load the latest uploaded image
3. The node automatically loads the newest image from the input folder
4. Connect to your workflow as usual

## Architecture

```
Photoshop Plugin (UXP)
    ↓ (File picker exports PNG)
    ↓
Helper Server (localhost:8765)
    ↓ (Forwards via HTTP/HTTPS)
    ↓
ComfyUI (Local or RunPod)
    ↓
Custom Nodes load images
```

## Configuration

- **Helper Server**: Runs on `http://localhost:8765`
- **ComfyUI URL**: Configurable in plugin (supports both local and RunPod URLs)
- **Image Upload**: Uses ComfyUI's `/upload/image` endpoint
- **Communication**: Helper server forwards via HTTP/HTTPS
- **Image Format**: PNG with transparency support

## Troubleshooting

### Helper server won't start
- Make sure you installed dependencies: `pip install -r requirements_helper.txt`
- Check if port 8765 is already in use: `lsof -i :8765` (macOS/Linux)
- Try a different port by editing `helper_server.py` (change `port=8765`)

### "Helper server not running" in plugin
- Start the helper server: `python helper_server.py`
- Make sure it shows "Starting server on http://localhost:8765"
- Check firewall settings aren't blocking localhost connections

### "Connection failed" to ComfyUI
- Verify ComfyUI is running and accessible
- For RunPod: Make sure you're using the correct proxy URL
- For local: Use `http://localhost:8188` (not https)
- Test manually: Open `http://localhost:8188/system_stats` in browser

### Images not appearing in ComfyUI node
- In the "Load Image from Photoshop" node, **toggle the refresh checkbox**
- Check ComfyUI's input folder for uploaded images
- Look at helper server terminal output for upload confirmation

### File picker appears every time
- This is expected behavior (workaround for UXP limitations)
- Choose any temporary location - file is auto-deleted after upload
- You can use the same folder each time for convenience

### "Error: invalid file token used" in Photoshop
- Make sure you're using the latest version of the plugin (index_helper.html)
- Try reloading the plugin in UXP Developer Tool
- Check that "Enable Generator" is enabled in Photoshop Preferences → Plugins
- If error persists, try restarting Photoshop

## Requirements

- **Local Machine**:
  - Adobe Photoshop 2021 or later
  - Python 3.7+ (for helper server)
  - Flask, flask-cors, requests (installed via requirements_helper.txt)

- **ComfyUI Server**:
  - ComfyUI installation
  - Standard Python dependencies (Pillow, torch, numpy)
