#!/usr/bin/env python3
"""
Simple test script to verify the bridge server is working
Run this to test without needing ComfyUI fully set up
"""

from flask import Flask, request, jsonify
import base64
from PIL import Image
import io
from datetime import datetime

app = Flask(__name__)

received_images = []


@app.route('/send_image', methods=['POST'])
def receive_image():
    """Test endpoint that mimics ComfyUI node behavior"""
    try:
        data = request.json
        image_data_b64 = data.get('image_data')
        layer_name = data.get('layer_name', 'Unknown')

        if not image_data_b64:
            return jsonify({"status": "error", "message": "No image data"}), 400

        # Decode and validate image
        image_bytes = base64.b64decode(image_data_b64)
        image = Image.open(io.BytesIO(image_bytes))

        image_id = len(received_images) + 1
        received_images.append({
            "id": image_id,
            "layer_name": layer_name,
            "size": f"{image.width}x{image.height}",
            "mode": image.mode,
            "timestamp": datetime.now().isoformat()
        })

        print(f"\n✓ Received image: {layer_name}")
        print(f"  ID: {image_id}")
        print(f"  Size: {image.width}x{image.height}")
        print(f"  Mode: {image.mode}")
        print(f"  Total received: {len(received_images)}")

        return jsonify({
            "status": "success",
            "message": "Image received",
            "image_id": image_id
        }), 200

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/status', methods=['GET'])
def status():
    """Status endpoint"""
    return jsonify({
        "status": "running",
        "received_images_count": len(received_images),
        "images": received_images
    }), 200


@app.route('/receive_image', methods=['POST'])
def send_to_photoshop():
    """Test endpoint for ComfyUI -> Photoshop direction"""
    try:
        data = request.json
        layer_name = data.get('layer_name', 'ComfyUI Output')
        print(f"\n✓ Would send to Photoshop: {layer_name}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("ComfyUI-Photoshop Bridge Test Server")
    print("=" * 60)
    print("\nStarting test server on port 8190...")
    print("\nTo test:")
    print("1. Open Photoshop and load the plugin")
    print("2. Open an image in Photoshop")
    print("3. Click 'Send to ComfyUI' in the plugin")
    print("4. You should see confirmation messages here")
    print("\nPress Ctrl+C to stop\n")
    print("=" * 60)

    app.run(host='0.0.0.0', port=8190, debug=True)
