"""
ComfyUI-Photoshop Bridge Nodes
Simple nodes to work with images uploaded from Photoshop
"""

import os
import time
import folder_paths
from PIL import Image
import numpy as np
import torch


class LoadImageFromPhotoshop:
    """
    Load images that were uploaded from Photoshop plugin
    This node provides a convenient way to access recent uploads

    To refresh the image list after uploading from Photoshop:
    - Change the 'refresh' number (increment it)
    - Or right-click the node and select 'Refresh'
    """

    @classmethod
    def INPUT_TYPES(cls):
        # Get list of images from input folder
        input_dir = folder_paths.get_input_directory()
        files = []

        if os.path.isdir(input_dir):
            files = [f for f in os.listdir(input_dir)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            # Sort by modification time, newest first
            files.sort(key=lambda x: os.path.getmtime(os.path.join(input_dir, x)), reverse=True)

        return {
            "required": {
                "image": (files if files else ["no_images_found.png"],),
            },
            "optional": {
                "refresh": ("INT", {"default": 0, "min": 0, "max": 999999, "tooltip": "Change this number to refresh the image list"}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"
    CATEGORY = "UnaCustom"

    def load_image(self, image, refresh=0):
        """Load the selected image"""
        input_dir = folder_paths.get_input_directory()
        image_path = os.path.join(input_dir, image)

        if not os.path.exists(image_path):
            # Return blank image if not found
            blank = torch.zeros((1, 64, 64, 3))
            mask = torch.zeros((1, 64, 64))
            return (blank, mask)

        img = Image.open(image_path)

        # Convert to RGB if needed
        if img.mode == 'I':
            img = img.point(lambda i: i * (1 / 255))
        if img.mode != 'RGB':
            img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')

        # Convert to numpy array
        img_array = np.array(img).astype(np.float32) / 255.0

        # Handle different image modes
        if img.mode == 'RGBA':
            image_tensor = torch.from_numpy(img_array[:, :, :3])[None,]
            mask = torch.from_numpy(img_array[:, :, 3])[None,]
        else:
            image_tensor = torch.from_numpy(img_array)[None,]
            mask = torch.zeros((1, img_array.shape[0], img_array.shape[1]))

        return (image_tensor, mask)

    @classmethod
    def IS_CHANGED(cls, image, refresh=0):
        """Force refresh - check for new files in input folder"""
        input_dir = folder_paths.get_input_directory()

        # Return the latest modification time + refresh counter
        # This will refresh when new images are added OR when refresh is changed
        if os.path.isdir(input_dir):
            try:
                files = [f for f in os.listdir(input_dir)
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                if files:
                    # Get the newest file's modification time
                    latest = max([os.path.getmtime(os.path.join(input_dir, f)) for f in files])
                    return (latest, refresh)
            except:
                pass

        return (time.time(), refresh)


class SaveImageToPhotoshop:
    """
    Save node optimized for sending back to Photoshop
    Images are saved in a format that can be easily picked up
    """

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
        """Save images to output folder"""
        results = []

        for idx, image in enumerate(images):
            # Convert tensor to PIL Image
            img_array = (image.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_array)

            # Generate filename
            filename = f"{filename_prefix}_{idx:04d}.png"
            filepath = os.path.join(self.output_dir, filename)

            # Save as PNG
            pil_image.save(filepath, format='PNG')

            results.append({
                "filename": filename,
                "subfolder": "",
                "type": "output"
            })

        return {"ui": {"images": results}}


# Register nodes with ComfyUI
NODE_CLASS_MAPPINGS = {
    "LoadImageFromPhotoshop": LoadImageFromPhotoshop,
    "SaveImageToPhotoshop": SaveImageToPhotoshop,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromPhotoshop": "Load Image from Photoshop",
    "SaveImageToPhotoshop": "Save Image to Photoshop",
}
