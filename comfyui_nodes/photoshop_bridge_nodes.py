"""
ComfyUI-Photoshop Bridge Nodes
Enables bidirectional image transfer between Photoshop and ComfyUI
"""

import os
import io
import base64
import threading
from flask import Flask, request, jsonify
from PIL import Image
import numpy as np
import torch
import folder_paths
import requests
from datetime import datetime

# Global variables for the Flask server
bridge_app = Flask(__name__)
bridge_server = None
received_images = {}


class LoadImageFromPhotoshop:
    """
    Receives images from Photoshop via HTTP and loads them into ComfyUI workflow
    """

    def __init__(self):
        self.type = "input"
        self.bridge_port = 8190
        self.latest_image_id = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "auto_refresh": (["enabled", "disabled"], {"default": "enabled"}),
                "bridge_port": ("INT", {"default": 8190, "min": 1024, "max": 65535}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK",)
    FUNCTION = "load_image"
    CATEGORY = "image/photoshop_bridge"

    def load_image(self, auto_refresh, bridge_port):
        """Load the most recently received image from Photoshop"""
        global received_images

        # Start the bridge server if not already running
        self._ensure_server_running(bridge_port)

        if not received_images:
            # Return a blank image if nothing received yet
            blank = torch.zeros((1, 64, 64, 3))
            mask = torch.zeros((1, 64, 64))
            return (blank, mask)

        # Get the most recent image
        latest_id = max(received_images.keys())
        image_data = received_images[latest_id]

        # Convert PIL Image to torch tensor
        img = image_data['image']
        img_array = np.array(img).astype(np.float32) / 255.0

        # Handle different image modes
        if img.mode == 'RGB':
            image_tensor = torch.from_numpy(img_array)[None,]
            mask = torch.zeros((1, img_array.shape[0], img_array.shape[1]))
        elif img.mode == 'RGBA':
            image_tensor = torch.from_numpy(img_array[:, :, :3])[None,]
            mask = torch.from_numpy(img_array[:, :, 3])[None,]
        else:
            # Convert to RGB if other mode
            img = img.convert('RGB')
            img_array = np.array(img).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(img_array)[None,]
            mask = torch.zeros((1, img_array.shape[0], img_array.shape[1]))

        return (image_tensor, mask)

    def _ensure_server_running(self, port):
        """Ensure the Flask server is running"""
        global bridge_server

        if bridge_server is None or not bridge_server.is_alive():
            self.bridge_port = port
            bridge_server = threading.Thread(
                target=self._run_server,
                args=(port,),
                daemon=True
            )
            bridge_server.start()
            print(f"[Photoshop Bridge] Server started on port {port}")

    def _run_server(self, port):
        """Run the Flask server"""
        bridge_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


class SendImageToPhotoshop:
    """
    Sends images from ComfyUI to Photoshop as new layers
    """

    def __init__(self):
        self.type = "output"
        self.photoshop_url = "http://localhost:8191"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "photoshop_port": ("INT", {"default": 8191, "min": 1024, "max": 65535}),
                "layer_name": ("STRING", {"default": "ComfyUI Output"}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "send_image"
    OUTPUT_NODE = True
    CATEGORY = "image/photoshop_bridge"

    def send_image(self, images, photoshop_port, layer_name):
        """Send image(s) to Photoshop"""

        results = []

        for idx, image in enumerate(images):
            # Convert tensor to PIL Image
            img_array = (image.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_array)

            # Convert to PNG bytes
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()

            # Encode as base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            # Send to Photoshop
            try:
                url = f"http://localhost:{photoshop_port}/receive_image"
                payload = {
                    "image_data": img_base64,
                    "layer_name": f"{layer_name}_{idx + 1}" if len(images) > 1 else layer_name,
                    "timestamp": datetime.now().isoformat()
                }

                response = requests.post(url, json=payload, timeout=10)

                if response.status_code == 200:
                    results.append({"status": "success", "index": idx})
                    print(f"[Photoshop Bridge] Image {idx + 1} sent successfully")
                else:
                    results.append({"status": "error", "index": idx, "message": response.text})
                    print(f"[Photoshop Bridge] Failed to send image {idx + 1}: {response.text}")

            except Exception as e:
                results.append({"status": "error", "index": idx, "message": str(e)})
                print(f"[Photoshop Bridge] Error sending image {idx + 1}: {str(e)}")

        return {"ui": {"results": results}}


# Flask routes for receiving images from Photoshop
@bridge_app.route('/send_image', methods=['POST'])
def receive_from_photoshop():
    """Endpoint to receive images from Photoshop"""
    global received_images

    try:
        data = request.json
        image_data_b64 = data.get('image_data')
        layer_name = data.get('layer_name', 'Photoshop Layer')

        if not image_data_b64:
            return jsonify({"status": "error", "message": "No image data provided"}), 400

        # Decode base64 image
        image_bytes = base64.b64decode(image_data_b64)
        image = Image.open(io.BytesIO(image_bytes))

        # Store the image with a timestamp ID
        image_id = len(received_images) + 1
        received_images[image_id] = {
            "image": image,
            "layer_name": layer_name,
            "timestamp": datetime.now().isoformat()
        }

        print(f"[Photoshop Bridge] Received image: {layer_name} (ID: {image_id})")

        return jsonify({
            "status": "success",
            "message": "Image received",
            "image_id": image_id
        }), 200

    except Exception as e:
        print(f"[Photoshop Bridge] Error receiving image: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@bridge_app.route('/status', methods=['GET'])
def status():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "received_images_count": len(received_images)
    }), 200


# Register nodes with ComfyUI
NODE_CLASS_MAPPINGS = {
    "LoadImageFromPhotoshop": LoadImageFromPhotoshop,
    "SendImageToPhotoshop": SendImageToPhotoshop,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromPhotoshop": "Load Image from Photoshop",
    "SendImageToPhotoshop": "Send Image to Photoshop",
}
