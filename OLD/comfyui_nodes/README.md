# ComfyUI Photoshop Bridge Nodes

Custom nodes for ComfyUI that enable bidirectional image transfer with Adobe Photoshop.

## Installation

1. Copy this entire folder to your ComfyUI custom_nodes directory:
   ```
   ComfyUI/custom_nodes/comfyui_photoshop_bridge/
   ```

2. Install required dependencies:
   ```bash
   cd ComfyUI/custom_nodes/comfyui_photoshop_bridge
   pip install flask pillow requests
   ```

3. Restart ComfyUI

## Nodes

### Load Image from Photoshop

Receives images sent from Photoshop via HTTP.

**Parameters:**
- `auto_refresh`: Enable/disable automatic refresh when new images arrive
- `bridge_port`: Port for the bridge server (default: 8190)

**Outputs:**
- `IMAGE`: The received image as a ComfyUI image tensor
- `MASK`: Alpha channel mask (if present)

### Send Image to Photoshop

Sends generated images back to Photoshop as new layers.

**Parameters:**
- `images`: Input images to send to Photoshop
- `photoshop_port`: Port where Photoshop plugin is listening (default: 8191)
- `layer_name`: Name for the new layer(s) in Photoshop

## How It Works

1. The **Load Image from Photoshop** node starts an HTTP server on port 8190
2. Photoshop plugin sends images to `http://localhost:8190/send_image`
3. The **Send Image to Photoshop** node sends images to `http://localhost:8191/receive_image`
4. Photoshop plugin receives and creates new layers

## Troubleshooting

- **Server won't start**: Check if port 8190 is already in use
- **Images not sending**: Ensure both ComfyUI and Photoshop are running
- **Connection refused**: Verify firewall settings allow local connections
