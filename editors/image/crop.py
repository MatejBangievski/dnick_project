from PIL import Image
from .base import ImageEditor

"""
Crop image to the box (left, top, right, bottom).
"""
class CropEditor(ImageEditor):
    def edit(self, image: Image.Image, **options) -> Image.Image:
        left   = options.get("left")
        top    = options.get("top")
        right  = options.get("right")
        bottom = options.get("bottom")

        if None in (left, top, right, bottom):
            raise ValueError("CropEditor requires left, top, right, bottom")

        return image.crop((left, top, right, bottom))