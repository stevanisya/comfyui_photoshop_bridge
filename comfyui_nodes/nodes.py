import os
import folder_paths
from PIL import Image
import numpy as np
import torch


class LoadFromPhotoshop:
    """Load an image synced from Photoshop via rsync."""

    SUBFOLDER = "photoshop_bridge"

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = os.path.join(folder_paths.get_input_directory(), cls.SUBFOLDER)
        files = []
        if os.path.isdir(input_dir):
            files = [f for f in os.listdir(input_dir)
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            files.sort(key=lambda x: os.path.getmtime(
                os.path.join(input_dir, x)), reverse=True)
        return {
            "required": {
                "image": (files if files else ["none"],),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"
    CATEGORY = "PhotoshopBridge"

    def load_image(self, image):
        input_dir = os.path.join(folder_paths.get_input_directory(), self.SUBFOLDER)
        image_path = os.path.join(input_dir, image)
        if not os.path.exists(image_path):
            blank = torch.zeros((1, 64, 64, 3))
            mask = torch.zeros((1, 64, 64))
            return (blank, mask)

        img = Image.open(image_path)
        if img.mode == 'I':
            img = img.point(lambda i: i * (1 / 255))
        has_alpha = img.mode == 'RGBA'
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')

        img_array = np.array(img).astype(np.float32) / 255.0
        if has_alpha:
            image_tensor = torch.from_numpy(img_array[:, :, :3])[None,]
            mask = torch.from_numpy(img_array[:, :, 3])[None,]
        else:
            image_tensor = torch.from_numpy(img_array)[None,]
            mask = torch.zeros((1, img_array.shape[0], img_array.shape[1]))

        return (image_tensor, mask)

    @classmethod
    def IS_CHANGED(cls, image):
        input_dir = os.path.join(folder_paths.get_input_directory(), cls.SUBFOLDER)
        image_path = os.path.join(input_dir, image)
        if os.path.exists(image_path):
            return os.path.getmtime(image_path)
        return float("inf")


NODE_CLASS_MAPPINGS = {
    "LoadFromPhotoshop": LoadFromPhotoshop,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadFromPhotoshop": "Load from Photoshop",
}
