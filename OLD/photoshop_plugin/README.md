# ComfyUI Bridge - Photoshop Plugin

UXP plugin for Adobe Photoshop that enables bidirectional image transfer with ComfyUI.

## Installation

### Method 1: UXP Developer Tool (Recommended for Development)

1. Install the Adobe UXP Developer Tool:
   - Open **Adobe Creative Cloud** desktop app
   - Go to **"All Apps"**
   - Search for **"UXP Developer Tools"** and install it
   - Enable **Developer Mode** when prompted
2. Open the UXP Developer Tool
3. Click "Add Plugin"
4. Navigate to this `photoshop_plugin` folder
5. Select the folder and click "Add"
6. Click "Load" to load the plugin into Photoshop

### Method 2: Manual Installation (For Distribution)

1. Package the plugin:
   ```bash
   # Zip the entire photoshop_plugin folder
   cd photoshop_plugin
   zip -r comfyui_bridge.zip *
   ```

2. Install in Photoshop:
   - Open Photoshop
   - Go to `Plugins` → `Manage Plugins`
   - Click "Load Plugin" and select the `.zip` file

## Usage

### Sending Images to ComfyUI

1. Open an image in Photoshop
2. Open the plugin panel: `Plugins` → `ComfyUI Bridge`
3. Select export type:
   - **Active Layer**: Exports only the currently selected layer
   - **Full Document**: Exports the entire document (flattened)
4. Click "Send to ComfyUI"
5. The image will appear in the "Load Image from Photoshop" node in ComfyUI

### Receiving Images from ComfyUI

1. In the plugin panel, click "Start Server"
2. In ComfyUI, add a "Send Image to Photoshop" node to your workflow
3. Run your ComfyUI workflow
4. Generated images will automatically appear as new layers in Photoshop

## Configuration

- **ComfyUI Bridge Port**: Port where ComfyUI is listening (default: 8190)
- **Listen Port**: Port where this plugin listens for incoming images (default: 8191)
- **Layer Name Prefix**: Prefix for imported layers (default: "ComfyUI")

## Troubleshooting

### "No active document" error
- Make sure you have an image open in Photoshop before sending

### Connection errors
- Verify ComfyUI is running
- Check that the ComfyUI Photoshop Bridge nodes are installed
- Ensure ports are not blocked by firewall
- Try clicking "Test Connection" to diagnose issues

### Server won't start
- Check if port 8191 is already in use
- Try changing the listen port in settings

### Images not appearing in Photoshop
- Make sure "Start Server" is enabled in the plugin
- Verify the port numbers match between ComfyUI and the plugin
- Check the browser console for errors (Help → Developer Tools)

## Requirements

- Adobe Photoshop 2021 or later
- ComfyUI with Photoshop Bridge nodes installed
- Network access to localhost

## Development

### Debugging

1. In Photoshop, go to `Help` → `Developer Tools`
2. Open the Console tab to see logs
3. Use `console.log()` in `main.js` for debugging

### Reloading Plugin

After making changes:
1. In UXP Developer Tool, click "Unload"
2. Click "Load" again
3. The plugin will reload with your changes

## Known Limitations

- Plugin uses simplified HTTP polling instead of a full server
- Large images may take time to transfer
- Only PNG format is supported
