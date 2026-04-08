# ComfyUI-Photoshop Bridge

> ⚠️ **Work in Progress** - This project is under active development. Some features may not work as expected yet.

A bridge to seamlessly transfer images between Adobe Photoshop and ComfyUI, powered by **[fal.ai](https://fal.ai)** cloud storage for reliable image transfer across local and remote setups.

## Features

- **Photoshop → ComfyUI**: Export layers or full document directly to ComfyUI
- **fal.ai Cloud Storage**: Upload images to fal.ai for fast, reliable transfer between Photoshop and ComfyUI — no matter where ComfyUI is running
- **Works with RunPod**: Supports remote ComfyUI instances directly
- **ComfyUI Nodes**: Custom nodes to load images from fal.ai URLs or the latest Photoshop exports
- **Fal Upload Node**: Dedicated ComfyUI node to upload images to fal.ai directly from workflows
- **ComfyUI → Photoshop**: Send generated images back to Photoshop as new layers *(coming soon)*

## Project Structure

```
comfyui_photoshop_bridge/
├── __init__.py                   # ComfyUI node loader
├── photoshop_bridge_nodes.py     # Custom node implementations (incl. fal.ai integration)
├── requirements.txt              # ComfyUI node dependencies
├── photoshop_plugin/             # Photoshop UXP plugin
│   ├── manifest.json
│   ├── main.js                   # Plugin logic (settings, fal.ai upload)
│   ├── index_helper.html         # Plugin UI
│   └── README.md
└── README.md
```

## How It Works

The plugin talks **directly to ComfyUI** (no helper server needed), and uses **fal.ai** for cloud-based image storage:

1. **Photoshop Plugin** exports image and uploads it directly to ComfyUI's `/upload/image` endpoint
2. **ComfyUI** receives the image, then uploads it to **fal.ai** storage server-side
3. **fal.ai** returns a CDN URL accessible from anywhere
4. **ComfyUI Nodes** load images via fal.ai URL or from the input folder

### Architecture

```
┌───────────────────┐         ┌──────────────────────┐
│   YOUR COMPUTER   │         │   RUNPOD / SERVER    │
│                   │         │                      │
│ ┌───────────────┐ │  HTTPS  │ ┌────────────────┐  │
│ │  Photoshop    │─┼─────────┼→│   ComfyUI      │  │
│ │  Plugin (UXP) │ │         │ │   + Nodes      │  │
│ └───────────────┘ │         │ └──────┬─────────┘  │
│                   │         │        │             │
└───────────────────┘         │        ▼             │
                              │ ┌────────────────┐  │
                              │ │  fal.ai Upload │  │
                              │ │  (server-side) │  │
                              │ └──────┬─────────┘  │
                              │        │             │
                              └────────┼─────────────┘
                                       ▼
                              ┌────────────────┐
                              │  fal.ai CDN    │
                              │  (cloud URL)   │
                              └────────────────┘
```

## Installation

### 1. ComfyUI Nodes (RunPod / Server)

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

### 2. Photoshop Plugin (Local Machine)

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

### 1. Configure Connection

In the Photoshop plugin panel:

1. Enter your ComfyUI URL:
   - **For RunPod**: `https://xxxxx-8188.proxy.runpod.net`
   - **For Local ComfyUI**: `http://localhost:8188`

2. Enter your **fal.ai API Key** (format: `key-xxxxxxxxxxxx`)

3. Click **"Test ComfyUI Connection"** to verify connectivity

### 2. Send Images from Photoshop to ComfyUI

1. Open an image in Photoshop
2. Choose export type:
   - **Active Layer**: Exports only the selected layer
   - **Full Document**: Exports the entire flattened image
3. Click **"Send to ComfyUI"**
4. **Choose where to save the temporary export** (any location is fine - the file will be auto-deleted after upload)
5. Progress: 📁 File picker → ⏳ Exporting → ⏳ Uploading → ✓ Uploaded!
6. The image is now in ComfyUI's input folder

### 3. Load in ComfyUI

In your ComfyUI workflow:

1. Add the **"Load Image from Photoshop"** node (category: UnaCustom)
2. Toggle the **refresh checkbox** to load the latest uploaded image
3. The node automatically loads the newest image from the input folder
4. Connect to your workflow as usual

## fal.ai Setup

The bridge uses [fal.ai](https://fal.ai) cloud storage to host uploaded images so they're accessible from anywhere (local or remote ComfyUI).

### Get a fal.ai API Key

1. Sign up at [fal.ai](https://fal.ai)
2. Go to your dashboard and generate an API key (format: `key-xxxxxxxxxxxx`)

### Configure the API Key

You can provide your fal.ai API key in multiple ways:

- **Photoshop Plugin**: Enter it in the "FAL API Key" field in the plugin panel
- **File**: Place a `fal_api_key.txt` file in the plugin data folder
- **ComfyUI config**: Create a `config.ini` in the `comfyui_nodes/` directory:
  ```ini
  [FAL]
  API_KEY = your-fal-api-key
  ```
- **Node input**: Pass it directly to the `FalImageUpload` node in your workflow

### ComfyUI Nodes for fal.ai

- **FalImageUpload**: Uploads images to fal.ai storage and returns the CDN URL. Accepts file paths, URLs, or image tensors as input.
- **LoadImageFromURL**: Loads images from any URL, including fal.ai storage URLs.

## Configuration

- **ComfyUI URL**: Configurable in plugin (supports both local and RunPod URLs)
- **fal.ai Storage**: Upload endpoint at `https://rest.fal.run/storage/upload`
- **Image Upload**: Uses ComfyUI's `/upload/image` endpoint, then fal.ai for cloud storage
- **Image Format**: PNG with transparency support

## Troubleshooting

### "Connection failed" to ComfyUI
- Verify ComfyUI is running and accessible
- For RunPod: Make sure you're using the correct proxy URL
- For local: Use `http://localhost:8188` (not https)
- Test manually: Open `http://localhost:8188/system_stats` in browser

### Images not appearing in ComfyUI node
- In the "Load Image from Photoshop" node, **toggle the refresh checkbox**
- Check ComfyUI's input folder for uploaded images
- Verify the fal.ai upload returned a valid URL

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

- **ComfyUI Server**:
  - ComfyUI installation
  - Standard Python dependencies (Pillow, torch, numpy)

- **fal.ai**:
  - Free or paid account at [fal.ai](https://fal.ai)
  - API key for cloud storage uploads
