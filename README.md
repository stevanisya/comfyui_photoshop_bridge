# ComfyUI-Photoshop Bridge

A bridge to seamlessly transfer images between Adobe Photoshop and ComfyUI.

## Features

- **Photoshop → ComfyUI**: Export layers or images directly to ComfyUI's Load Image node
- **ComfyUI → Photoshop**: Send generated images back to Photoshop as new layers

## Project Structure

```
comfyui_photoshop_bridge/
├── comfyui_nodes/          # ComfyUI custom nodes
│   ├── __init__.py
│   ├── photoshop_bridge_nodes.py
│   └── README.md
├── photoshop_plugin/       # Photoshop UXP plugin
│   ├── manifest.json
│   ├── main.js
│   ├── index.html
│   └── README.md
└── README.md
```

## Installation

### ComfyUI Nodes (RunPod / Server)

SSH into your ComfyUI instance and run:

```bash
# Navigate to ComfyUI custom_nodes folder
cd /workspace/ComfyUI/custom_nodes

# Clone the repository
git clone https://github.com/stevanisya/comfyui_photoshop_bridge.git

# Install Python dependencies
cd comfyui_photoshop_bridge/comfyui_nodes
pip install -r requirements.txt

# Restart ComfyUI
cd /workspace/ComfyUI
python main.py
```

### Photoshop Plugin (Local Machine)

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

### Configure Connection

In the Photoshop plugin panel:

1. **For RunPod**: Paste your ComfyUI URL
   ```
   https://xxxxx-8188.proxy.runpod.net
   ```

2. **For Local ComfyUI**: Use
   ```
   http://localhost:8188
   ```

3. Click **"Test Connection"** to verify
   - ✓ Should show "Connected to ComfyUI!"

### Sending Images from Photoshop to ComfyUI

1. Open an image in Photoshop
2. Choose export type:
   - **Active Layer**: Exports only the selected layer
   - **Full Document**: Exports the entire flattened image
3. Click **"Send to ComfyUI"**
4. Status will show: ⏳ Exporting → ⏳ Uploading → ✓ Uploaded!
5. The image is now in ComfyUI's input folder and can be used in workflows

## Configuration

- **ComfyUI URL**: Configurable in plugin (supports both local and RunPod URLs)
- **Image Upload**: Uses ComfyUI's built-in `/upload/image` endpoint
- **Communication**: HTTP REST API (HTTPS for RunPod)
- **Image Format**: PNG

## Requirements

- ComfyUI
- Adobe Photoshop 2021 or later
- Python 3.x
- Node.js (for UXP plugin development)
