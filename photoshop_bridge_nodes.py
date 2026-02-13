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
    Automatically loads the newest image uploaded from Photoshop
    No manual selection needed - always uses the most recent upload
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"
    CATEGORY = "UnaCustom"

    def load_image(self):
        """Load the newest image from input folder"""
        input_dir = folder_paths.get_input_directory()

        # Get all image files
        if not os.path.isdir(input_dir):
            # Return blank image if folder doesn't exist
            blank = torch.zeros((1, 64, 64, 3))
            mask = torch.zeros((1, 64, 64))
            return (blank, mask)

        files = [f for f in os.listdir(input_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

        if not files:
            # Return blank image if no images found
            blank = torch.zeros((1, 64, 64, 3))
            mask = torch.zeros((1, 64, 64))
            return (blank, mask)

        # Sort by modification time, newest first
        files.sort(key=lambda x: os.path.getmtime(os.path.join(input_dir, x)), reverse=True)

        # Get the newest file
        newest_image = files[0]
        image_path = os.path.join(input_dir, newest_image)

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
    def IS_CHANGED(cls):
        """Always check for newest file - auto-refreshes when new images are uploaded"""
        input_dir = folder_paths.get_input_directory()

        # Return the latest modification time to trigger refresh when new files are added
        if os.path.isdir(input_dir):
            try:
                files = [f for f in os.listdir(input_dir)
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                if files:
                    # Get the newest file's modification time
                    latest = max([os.path.getmtime(os.path.join(input_dir, f)) for f in files])
                    return latest
            except:
                pass

        return time.time()


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
