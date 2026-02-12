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

### ComfyUI Nodes
1. Copy the `comfyui_nodes` folder to `ComfyUI/custom_nodes/comfyui_photoshop_bridge/`
2. Restart ComfyUI

### Photoshop Plugin
1. Open the UXP Developer Tool
2. Load the `photoshop_plugin` folder as a plugin
3. Enable the plugin in Photoshop

## Usage

### Sending from Photoshop to ComfyUI
1. Open an image in Photoshop
2. Select a layer or use the active document
3. Click "Send to ComfyUI" in the plugin panel
4. The image will appear in the "Load Image from Photoshop" node

### Sending from ComfyUI to Photoshop
1. Connect your workflow to a "Send to Photoshop" node
2. Run the workflow
3. The generated image will automatically appear as a new layer in Photoshop

## Configuration

- Default ComfyUI Bridge Port: `8190` (configurable in the custom nodes)
- Communication: HTTP REST API

## Requirements

- ComfyUI
- Adobe Photoshop 2021 or later
- Python 3.x
- Node.js (for UXP plugin development)
