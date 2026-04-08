# Quick Start Guide

Get up and running with the ComfyUI-Photoshop Bridge in 5 minutes!

## Prerequisites

- ✅ ComfyUI installed and running
- ✅ Adobe Photoshop 2021 or later
- ✅ Python 3.8+ (usually comes with ComfyUI)
- ✅ Adobe UXP Developer Tool (install via Adobe Creative Cloud app)

## Step 1: Install ComfyUI Nodes

### Option A: Manual Installation

1. Copy the `comfyui_nodes` folder to your ComfyUI installation:
   ```bash
   cp -r comfyui_nodes /path/to/ComfyUI/custom_nodes/comfyui_photoshop_bridge
   ```

2. Install dependencies:
   ```bash
   cd /path/to/ComfyUI/custom_nodes/comfyui_photoshop_bridge
   pip install -r requirements.txt
   ```

3. Restart ComfyUI

### Option B: Symlink (Recommended for Development)

```bash
ln -s "$(pwd)/comfyui_nodes" /path/to/ComfyUI/custom_nodes/comfyui_photoshop_bridge
cd /path/to/ComfyUI/custom_nodes/comfyui_photoshop_bridge
pip install -r requirements.txt
```

## Step 2: Install Photoshop Plugin

### Install UXP Developer Tool (if you haven't already)
1. Open **Adobe Creative Cloud** desktop app
2. Go to **"All Apps"** section
3. Search for **"UXP Developer Tools"**
4. Click **"Install"**
5. Enable **Developer Mode** when prompted (required)

### Load the Plugin
1. Open **UXP Developer Tool** (from Creative Cloud or Applications)
2. Click **"Add Plugin"**
3. Navigate to and select the `photoshop_plugin` folder
4. Click **"Load"** and select your Photoshop version
5. The plugin panel should appear in Photoshop under **Plugins → ComfyUI Bridge**

## Step 3: Test the Connection

### Test 1: Photoshop → ComfyUI

1. **In ComfyUI:**
   - Create a new workflow
   - Add a "Load Image from Photoshop" node (search in node menu)
   - The node will automatically start a server on port 8190

2. **In Photoshop:**
   - Open any image
   - Open the ComfyUI Bridge plugin panel (`Plugins` → `ComfyUI Bridge`)
   - Click "Test Connection" - you should see "✓ Connection successful!"
   - Click "Send to ComfyUI"
   - Your image should appear in the ComfyUI node!

### Test 2: ComfyUI → Photoshop

1. **In the Plugin:**
   - Click "Start Server" (listen port: 8191)

2. **In ComfyUI:**
   - Add a "Send Image to Photoshop" node
   - Connect it to your workflow output
   - Run the workflow
   - The generated image should appear as a new layer in Photoshop!

## Architecture

```
┌─────────────────┐                          ┌──────────────────┐
│   Photoshop     │                          │     ComfyUI      │
│                 │                          │                  │
│  UXP Plugin     │ ──HTTP POST (8190)────→ │ Load Image Node  │
│  (JavaScript)   │    (sends PNG base64)    │ (Python + Flask) │
│                 │                          │                  │
│  HTTP Listener  │ ←──HTTP POST (8191)──── │ Send Image Node  │
│  (Port 8191)    │   (receives PNG base64)  │ (Python)         │
└─────────────────┘                          └──────────────────┘
```

## Common Issues

### Port Already in Use
```bash
# Check what's using port 8190 or 8191
lsof -i :8190
lsof -i :8191

# Kill the process if needed
kill -9 <PID>
```

### Dependencies Not Found
```bash
# Make sure you're in the ComfyUI Python environment
cd /path/to/ComfyUI
source venv/bin/activate  # if using venv
pip install flask pillow requests
```

### Plugin Not Appearing
- Make sure you're using Photoshop 2021 or later
- Check UXP Developer Tool for error messages
- Try reloading the plugin

### Images Not Transferring
- Verify both ComfyUI and Photoshop are running
- Check firewall isn't blocking localhost connections
- Use "Test Connection" button to diagnose
- Check the console logs in both applications

## Next Steps

- Explore combining with other ComfyUI nodes (ControlNet, upscalers, etc.)
- Automate your workflow with batch processing
- Customize layer naming and organization
- Add custom preprocessing in the plugin

## Support

- Report issues: [GitHub Issues](https://github.com/yourusername/comfyui-photoshop-bridge/issues)
- ComfyUI Discord: [Join here](https://discord.gg/comfyui)
- Photoshop UXP Docs: [developer.adobe.com](https://developer.adobe.com/photoshop/uxp/)
