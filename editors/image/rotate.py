from PIL import Image
from .base import ImageEditor

class RotateEditor(ImageEditor):
    def edit(self, image: Image.Image, **options) -> Image.Image:
        """
        Rotate image by a custom angle (passed in options['angle']).
        """
        angle = options.get("angle")
        if angle is None:
            raise ValueError("RotateEditor requires an 'angle' in options")
        return image.rotate(angle, expand=True)

    def rotate_90(self, image: Image.Image) -> Image.Image:
        return image.rotate(90, expand=True)

    def rotate_180(self, image: Image.Image) -> Image.Image:
        return image.rotate(180, expand=True)

    def rotate_270(self, image: Image.Image) -> Image.Image:
        return image.rotate(270, expand=True)
