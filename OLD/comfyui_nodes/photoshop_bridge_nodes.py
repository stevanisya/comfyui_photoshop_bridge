"""
ComfyUI-Photoshop Bridge Nodes
"""

import os
import io
import tempfile
import configparser
import requests
import folder_paths
from PIL import Image
import numpy as np
import torch


# ── API route: server-side fal.ai upload ──────────────────────────────────────
try:
    from server import PromptServer
    from aiohttp import web

    CORS_HEADERS = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    @PromptServer.instance.routes.options("/photoshop_bridge/fal_upload")
    async def fal_upload_preflight(request):
        return web.Response(headers=CORS_HEADERS)

    @PromptServer.instance.routes.post("/photoshop_bridge/fal_upload")
    async def fal_upload(request):
        import asyncio
        data     = await request.json()
        filename = data.get("filename", "").strip()
        fal_key  = data.get("fal_key", "").strip()

        if not filename or not fal_key:
            return web.json_response({"error": "Missing filename or fal_key"}, status=400, headers=CORS_HEADERS)

        input_dir = folder_paths.get_input_directory()
        file_path = os.path.join(input_dir, filename)

        if not os.path.exists(file_path):
            return web.json_response({"error": f"File not found: {filename}"}, status=404, headers=CORS_HEADERS)

        print(f"[PhotoshopBridge] Uploading {filename} to fal.ai...")

        def do_upload():
            with open(file_path, "rb") as f:
                file_data = f.read()
            return requests.post(
                "https://rest.fal.run/storage/upload",
                headers={
                    "Authorization": f"Key {fal_key}",
                    "Content-Type": "image/png",
                    "X-Fal-File-Name": filename,
                },
                data=file_data,
                timeout=60,
            )

        resp = await asyncio.get_event_loop().run_in_executor(None, do_upload)

        if not resp.ok:
            print(f"[PhotoshopBridge] Fal upload failed: {resp.status_code} {resp.text}")
            return web.json_response(
                {"error": f"Fal upload failed ({resp.status_code}): {resp.text}"},
                status=500, headers=CORS_HEADERS
            )

        result = resp.json()
        url = result.get("url") or result.get("file_url") or result.get("cdn_url")
        print(f"[PhotoshopBridge] Fal upload success: {url}")
        return web.json_response({"url": url}, headers=CORS_HEADERS)

except Exception as e:
    print(f"[PhotoshopBridge] Could not register API route: {e}")


# ── Shared image loading helper ────────────────────────────────────────────────
def _load_image_from_url(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    img = Image.open(io.BytesIO(response.content))
    if img.mode == 'I':
        img = img.point(lambda i: i * (1 / 255))
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')
    img_array = np.array(img).astype(np.float32) / 255.0
    if img.mode == 'RGBA':
        image_tensor = torch.from_numpy(img_array[:, :, :3])[None,]
        mask = torch.from_numpy(img_array[:, :, 3])[None,]
    else:
        image_tensor = torch.from_numpy(img_array)[None,]
        mask = torch.zeros((1, img_array.shape[0], img_array.shape[1]))
    return image_tensor, mask


# ── Nodes ──────────────────────────────────────────────────────────────────────

class LoadImageFromURL:
    """
    Load an image from a URL (e.g. fal.ai storage).
    Paste the URL the Photoshop plugin gives you after uploading.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_from_url"
    CATEGORY = "UnaCustom"

    def load_from_url(self, url):
        url = url.strip()
        if not url:
            blank = torch.zeros((1, 64, 64, 3))
            mask = torch.zeros((1, 64, 64))
            return (blank, mask)
        return _load_image_from_url(url)

    @classmethod
    def IS_CHANGED(cls, url):
        return url


class LoadImageFromPhotoshop:
    """Load images uploaded from Photoshop via ComfyUI's input folder."""

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = []
        if os.path.isdir(input_dir):
            files = [f for f in os.listdir(input_dir)
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            files.sort(key=lambda x: os.path.getmtime(os.path.join(input_dir, x)), reverse=True)
        return {"required": {"image": (files if files else ["no_images_found.png"],)}}

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"
    CATEGORY = "UnaCustom"

    def load_image(self, image):
        input_dir = folder_paths.get_input_directory()
        image_path = os.path.join(input_dir, image)
        if not os.path.exists(image_path):
            blank = torch.zeros((1, 64, 64, 3))
            mask = torch.zeros((1, 64, 64))
            return (blank, mask)
        img = Image.open(image_path)
        if img.mode == 'I':
            img = img.point(lambda i: i * (1 / 255))
        if img.mode != 'RGB':
            img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')
        img_array = np.array(img).astype(np.float32) / 255.0
        if img.mode == 'RGBA':
            image_tensor = torch.from_numpy(img_array[:, :, :3])[None,]
            mask = torch.from_numpy(img_array[:, :, 3])[None,]
        else:
            image_tensor = torch.from_numpy(img_array)[None,]
            mask = torch.zeros((1, img_array.shape[0], img_array.shape[1]))
        return (image_tensor, mask)

    @classmethod
    def IS_CHANGED(cls, image):
        input_dir = folder_paths.get_input_directory()
        image_path = os.path.join(input_dir, image)
        if os.path.exists(image_path):
            return os.path.getmtime(image_path)
        return float("inf")


class SaveImageToPhotoshop:
    """Save node optimized for sending back to Photoshop."""

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "PhotoshopBridge"}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "UnaCustom"

    def save_images(self, images, filename_prefix="PhotoshopBridge"):
        results = []
        for idx, image in enumerate(images):
            img_array = (image.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_array)
            filename = f"{filename_prefix}_{idx:04d}.png"
            filepath = os.path.join(self.output_dir, filename)
            pil_image.save(filepath, format='PNG')
            results.append({"filename": filename, "subfolder": "", "type": "output"})
        return {"ui": {"images": results}}


class FalImageUpload:
    """
    Upload an image to fal.ai storage and return the URL.
    Accepts any input type: file path, URL, IMAGE tensor, or object with save_to().
    """

    CATEGORY = "UnaCustom"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_path": ("*",),
            },
            "optional": {
                "fal_api_key": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("image_url",)
    FUNCTION = "upload"

    def _load_config(self, api_key_override=None):
        if api_key_override:
            return api_key_override.strip()
        cfg = configparser.ConfigParser()
        cfg_path = os.path.join(os.path.dirname(__file__), "config.ini")
        cfg.read(cfg_path)
        if "FAL" not in cfg or "API_KEY" not in cfg["FAL"]:
            raise RuntimeError("Fal.ai API Key not found in config.ini")
        api_key = cfg["FAL"]["API_KEY"]
        if not api_key:
            raise RuntimeError("Fal.ai API Key is empty in config.ini")
        return api_key.strip()

    def _upload_to_fal(self, file_path, api_key):
        with open(file_path, "rb") as f:
            file_data = f.read()
        filename = os.path.basename(file_path)
        resp = requests.post(
            "https://rest.fal.run/storage/upload",
            headers={
                "Authorization": f"Key {api_key}",
                "Content-Type": "image/png",
                "X-Fal-File-Name": filename,
            },
            data=file_data,
            timeout=60,
        )
        if not resp.ok:
            raise RuntimeError(f"Fal upload failed ({resp.status_code}): {resp.text}")
        result = resp.json()
        url = result.get("url") or result.get("file_url") or result.get("cdn_url")
        if not url:
            raise RuntimeError(f"No URL in fal response: {result}")
        return url

    def upload(self, image_path, fal_api_key=None):
        api_key = self._load_config(fal_api_key)

        # Handle list of paths
        if isinstance(image_path, list):
            if len(image_path) > 0:
                image_path = image_path[0]
            else:
                image_path = ""

        # Handle IMAGE tensor from ComfyUI
        if isinstance(image_path, torch.Tensor):
            print("[PhotoshopBridge Fal] Input is a torch tensor, saving to temp file...")
            try:
                img_array = (image_path.squeeze(0).cpu().numpy() * 255).astype(np.uint8)
                pil_image = Image.fromarray(img_array)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    temp_path = f.name
                pil_image.save(temp_path, format="PNG")
                image_path = temp_path
            except Exception as e:
                print(f"[PhotoshopBridge Fal] Failed to save tensor: {e}")
                return (f"Error: {e}",)

        # Handle objects with save_to method
        elif not isinstance(image_path, str):
            print(f"[PhotoshopBridge Fal] Input is object: {type(image_path)}")

            if hasattr(image_path, "save_to") and callable(image_path.save_to):
                print("[PhotoshopBridge Fal] Object has save_to method. Saving to temp file...")
                try:
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                        temp_path = f.name
                    image_path.save_to(temp_path)
                    image_path = temp_path
                except Exception as e:
                    print(f"[PhotoshopBridge Fal] Failed to save image object: {e}")

            elif not isinstance(image_path, str):
                for attr in ['path', 'file_path', 'filename', 'url']:
                    if hasattr(image_path, attr):
                        val = getattr(image_path, attr)
                        if val and isinstance(val, str):
                            print(f"[PhotoshopBridge Fal] Found path in '{attr}': {val}")
                            image_path = val
                            break

            if not isinstance(image_path, str):
                print(f"[PhotoshopBridge Fal] Object attributes: {dir(image_path)}")
                image_path = str(image_path)

        if not image_path:
            return ("",)

        # Already a URL — pass through
        if image_path.startswith("http"):
            return (image_path,)

        if not os.path.exists(image_path):
            print(f"[PhotoshopBridge Fal] File not found: {image_path}")
            return ("",)

        print(f"[PhotoshopBridge Fal] Uploading {image_path}...")
        try:
            url = self._upload_to_fal(image_path, api_key)
            print(f"[PhotoshopBridge Fal] Upload Success: {url}")
            return (url,)
        except Exception as e:
            print(f"[PhotoshopBridge Fal] Upload failed: {e}")
            return (f"Error: {e}",)


# ── Register ───────────────────────────────────────────────────────────────────
NODE_CLASS_MAPPINGS = {
    "LoadImageFromURL": LoadImageFromURL,
    "LoadImageFromPhotoshop": LoadImageFromPhotoshop,
    "SaveImageToPhotoshop": SaveImageToPhotoshop,
    "FalImageUpload": FalImageUpload,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromURL": "Load Image from URL (Photoshop Bridge)",
    "LoadImageFromPhotoshop": "Load Image from Photoshop",
    "SaveImageToPhotoshop": "Save Image to Photoshop",
    "FalImageUpload": "Fal Image Upload (Photoshop Bridge)",
}
