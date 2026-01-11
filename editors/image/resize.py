from PIL import Image
from .base import ImageEditor

"""
Resize image to (width, height). Supports upscaling.
"""
class ResizeEditor(ImageEditor):
    def edit(self, image: Image.Image, **options) -> Image.Image:
        width = options.get("width")
        height = options.get("height")

        if width is None or height is None:
            raise ValueError("ResizeEditor requires width and height")

        return image.resize((width, height), Image.LANCZOS)
