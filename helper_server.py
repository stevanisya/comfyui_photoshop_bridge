#!/usr/bin/env python3
"""
ComfyUI-Photoshop Bridge Helper Server

This local server acts as a bridge between the Photoshop plugin and ComfyUI.
It receives images from Photoshop and forwards them to your ComfyUI instance.

Usage:
    python helper_server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for UXP plugin requests

# Configuration
DEFAULT_COMFYUI_URL = "http://localhost:8188"
comfyui_url = os.environ.get("COMFYUI_URL", DEFAULT_COMFYUI_URL)

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "server": "ComfyUI Bridge Helper"}), 200

@app.route("/upload", methods=["POST"])
def upload_to_comfyui():
    """
    Receive image from Photoshop plugin and forward to ComfyUI
    """
    try:
        # Check if file is in request
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400

        # Get ComfyUI URL from request or use default
        target_url = request.form.get('comfyui_url', comfyui_url)
        if target_url.endswith('/'):
            target_url = target_url[:-1]

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Received image: {file.filename}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Forwarding to: {target_url}/upload/image")

        # Forward to ComfyUI
        files = {'image': (file.filename, file.stream, file.content_type)}
        data = {'overwrite': 'true'}

        response = requests.post(
            f"{target_url}/upload/image",
            files=files,
            data=data,
            timeout=30
        )

        if response.ok:
            result = response.json()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Upload successful: {result.get('name', file.filename)}")
            return jsonify({
                "success": True,
                "filename": result.get('name', file.filename),
                "message": "Image uploaded to ComfyUI"
            }), 200
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Upload failed: {response.status_code}")
            return jsonify({
                "error": f"ComfyUI returned status {response.status_code}",
                "details": response.text
            }), response.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Cannot connect to ComfyUI",
            "details": f"Is ComfyUI running at {target_url}?"
        }), 503
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/test-comfyui", methods=["GET"])
def test_comfyui():
    """Test connection to ComfyUI"""
    try:
        target_url = request.args.get('url', comfyui_url)
        if target_url.endswith('/'):
            target_url = target_url[:-1]

        response = requests.get(f"{target_url}/system_stats", timeout=5)

        if response.ok:
            return jsonify({
                "success": True,
                "message": "Connected to ComfyUI",
                "url": target_url
            }), 200
        else:
            return jsonify({
                "error": f"ComfyUI returned status {response.status_code}"
            }), response.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Cannot connect to ComfyUI",
            "url": target_url
        }), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("=" * 60)
    print("ComfyUI-Photoshop Bridge Helper Server")
    print("=" * 60)
    print(f"Starting server on http://localhost:8765")
    print(f"Default ComfyUI URL: {comfyui_url}")
    print("\nEndpoints:")
    print("  GET  /health        - Health check")
    print("  POST /upload        - Receive and forward images")
    print("  GET  /test-comfyui  - Test ComfyUI connection")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)

    app.run(host="0.0.0.0", port=8765, debug=False)
