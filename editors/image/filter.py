from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from .base import ImageEditor

class FilterEditor(ImageEditor):
    def edit(self, image: Image.Image, **options) -> Image.Image:
        """
        Apply a custom filter dynamically.

        Usage:
            editor.edit(image, filter="brighten")
            editor.edit(image, filter="brighten", factor=2.0)

        Each filter has a default preset, but custom parameters
        may be passed via **options.
        """
        filter_name = options.get("filter")
        if filter_name is None:
            raise ValueError("FilterEditor requires 'filter' in options")

        filter_name = filter_name.lower()

        # ---------------------------
        # Grayscale
        # ---------------------------
        if filter_name == "grayscale":
            return ImageOps.grayscale(image)

        # ---------------------------
        # Invert (supports RGBA)
        # ---------------------------
        elif filter_name == "invert":
            if image.mode == "RGBA":
                r, g, b, a = image.split()
                rgb_image = Image.merge("RGB", (r, g, b))
                inverted = ImageOps.invert(rgb_image)
                r2, g2, b2 = inverted.split()
                return Image.merge("RGBA", (r2, g2, b2, a))
            return ImageOps.invert(image)

        # ---------------------------
        # Sepia (preset or intensity)
        # intensity 0–1 (default 1)
        # ---------------------------
        elif filter_name == "sepia":
            intensity = options.get("intensity", 1.0)

            # convert to grayscale
            gray = ImageOps.grayscale(image)
            sepia = ImageOps.colorize(gray, "#704214", "#FFC0A0")

            if intensity < 1.0:
                # blend original + sepia
                return Image.blend(image.convert("RGB"), sepia.convert("RGB"), intensity)

            return sepia

        # ---------------------------
        # Brightness
        # default factor = 1.5
        # ---------------------------
        elif filter_name == "brighten":
            factor = options.get("factor", 1.5)
            enhancer = ImageEnhance.Brightness(image)
            return enhancer.enhance(factor)

        # ---------------------------
        # Contrast
        # default factor = 1.5
        # ---------------------------
        elif filter_name == "contrast":
            factor = options.get("factor", 1.5)
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(factor)

        # ---------------------------
        # Blur
        # default radius = 2
        # ---------------------------
        elif filter_name == "blur":
            radius = options.get("radius", 2)
            return image.filter(ImageFilter.GaussianBlur(radius))

        # ---------------------------
        # Sharpen
        # default intensity = 1 (can stack sharpen filter)
        # ---------------------------
        elif filter_name == "sharpen":
            strength = options.get("strength", 1)

            result = image
            for _ in range(strength):
                result = result.filter(ImageFilter.SHARPEN)
            return result

        # ---------------------------
        # Edge Enhance
        # default intensity = 1 (stackable)
        # ---------------------------
        elif filter_name == "edge_enhance":
            strength = options.get("strength", 1)

            result = image
            for _ in range(strength):
                result = result.filter(ImageFilter.EDGE_ENHANCE)
            return result

        # ---------------------------
        # Unknown filter
        # ---------------------------
        else:
            raise ValueError(f"Unknown filter: {filter_name}")
