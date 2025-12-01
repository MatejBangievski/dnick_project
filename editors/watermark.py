from PIL import Image, ImageEnhance
from editors.base import ImageEditor  # adjust to your actual import

class WatermarkEditor(ImageEditor):
    """
    Add a PNG watermark to an image.
    Supports default preset positions and custom coordinates.
    Allows opacity adjustment.
    """

    def edit(self, image: Image.Image, **options) -> Image.Image:
        watermark_path = options.get("watermark")
        if not watermark_path:
            raise ValueError("WatermarkEditor requires 'watermark' path in options.")

        # Load watermark
        watermark = Image.open(watermark_path)

        # Constraint: watermark must be PNG
        if not watermark_path.lower().endswith(".png"):
            raise ValueError("Watermark must be a PNG file with transparency.")

        # Force RGBA for transparency operations
        image = image.convert("RGBA")
        watermark = watermark.convert("RGBA")

        # Opacity (default 0.5)
        opacity = options.get("opacity", 0.5)
        watermark = self._apply_opacity(watermark, opacity)

        # Resize watermark if requested
        max_width = options.get("max_width")
        max_height = options.get("max_height")
        if max_width or max_height:
            watermark = self._resize_watermark(watermark, max_width, max_height)

        # Positioning
        position = options.get("position", "bottom-right")
        if isinstance(position, tuple):
            # custom absolute (x, y)
            x, y = position
        else:
            x, y = self._preset_position(position, image, watermark)

        # Create a new image to blend
        result = image.copy()
        result.alpha_composite(watermark, (x, y))
        return result

    # --------------------------
    # Helper: adjust transparency
    # --------------------------
    def _apply_opacity(self, watermark: Image.Image, opacity: float):
        if opacity >= 1:
            return watermark
        if opacity <= 0:
            opacity = 0

        alpha = watermark.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        watermark.putalpha(alpha)
        return watermark

    # --------------------------
    # Helper: optional resizing
    # --------------------------
    def _resize_watermark(self, watermark, max_w, max_h):
        w, h = watermark.size
        if max_w and w > max_w:
            scale = max_w / w
            w = max_w
            h = int(h * scale)

        if max_h and h > max_h:
            scale = max_h / h
            h = max_h
            w = int(w * scale)

        return watermark.resize((w, h), Image.LANCZOS)

    # --------------------------
    # Helper: preset positions
    # --------------------------
    def _preset_position(self, name, base, wm):
        bw, bh = base.size
        ww, wh = wm.size

        margin = 20  # default padding

        name = name.lower()

        if name == "top-left":
            return (margin, margin)

        elif name == "top-right":
            return (bw - ww - margin, margin)

        elif name == "bottom-left":
            return (margin, bh - wh - margin)

        elif name == "bottom-right":
            return (bw - ww - margin, bh - wh - margin)

        elif name == "center":
            return ((bw - ww) // 2, (bh - wh) // 2)

        elif name == "tile":
            # special case — handled elsewhere
            return (0, 0)

        else:
            raise ValueError(f"Unknown preset position '{name}'. Use tuple (x, y) for custom position.")
