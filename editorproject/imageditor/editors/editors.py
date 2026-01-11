from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont
from .base import ImageEditor  # Now imports from the new base.py
import os

"""
Crop image to the box (left, top, right, bottom).
"""


class CropEditor(ImageEditor):
    def edit(self, image: Image.Image, **options) -> Image.Image:
        left = options.get("left")
        top = options.get("top")
        right = options.get("right")
        bottom = options.get("bottom")

        if None in (left, top, right, bottom):
            raise ValueError("CropEditor requires left, top, right, bottom")

        return image.crop((left, top, right, bottom))


"""
Resize image to (width, height). Supports upscaling.
"""


class ResizeEditor(ImageEditor):
    def edit(self, image: Image.Image, **options) -> Image.Image:
        width = options.get("width")
        height = options.get("height")

        if width is None or height is None:
            raise ValueError("ResizeEditor requires width and height")

        # OPTIMIZATION: Use LANCZOS for high-quality downsampling, BICUBIC for upsampling
        target_size = (width, height)
        current_size = image.size

        # Choose appropriate resampling based on whether we're upscaling or downscaling
        # Handle both old and new Pillow API versions
        try:
            LANCZOS = Image.Resampling.LANCZOS
            BICUBIC = Image.Resampling.BICUBIC
        except AttributeError:
            LANCZOS = Image.LANCZOS
            BICUBIC = Image.BICUBIC

        if width > current_size[0] or height > current_size[1]:
            # Upscaling - BICUBIC is faster and good enough
            return image.resize(target_size, BICUBIC)
        else:
            # Downscaling - LANCZOS for best quality
            return image.resize(target_size, LANCZOS)


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


class FilterEditor(ImageEditor):
    def edit(self, image: Image.Image, **options) -> Image.Image:
        """
        Apply a custom filter dynamically. Aligned with config.py parameters:
        'factor' for enhancement filters.
        'radius' for blur filters.
        """
        filter_name = options.get("filter")
        if filter_name is None:
            raise ValueError("FilterEditor requires 'filter' in options")

        filter_name = filter_name.lower()

        # NOTE: Factors are typically 0.0 to 5.0 in your config.py

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
        # Sepia (simple colorize)
        # ---------------------------
        elif filter_name == "sepia":
            # NOTE: We ignore the 'factor' option here as ImageOps.colorize doesn't natively use it.
            gray = ImageOps.grayscale(image)
            return ImageOps.colorize(gray, "#704214", "#FFC0A0")

        # ---------------------------
        # Brightness (uses 'factor' from config)
        # ---------------------------
        elif filter_name == "brighten":
            factor = options.get("factor", 1.5)
            enhancer = ImageEnhance.Brightness(image)
            return enhancer.enhance(factor)

        # ---------------------------
        # Contrast (uses 'factor' from config)
        # ---------------------------
        elif filter_name == "contrast":
            factor = options.get("factor", 1.5)
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(factor)

        # ---------------------------
        # Blur (uses 'radius' from config)
        # ---------------------------
        elif filter_name == "blur":
            radius = options.get("radius", 2)
            # OPTIMIZATION: Clamp radius to prevent excessive processing time
            radius = min(max(0, radius), 50)  # Limit to 0-50 range
            if radius == 0:
                return image
            return image.filter(ImageFilter.GaussianBlur(radius))

        # ---------------------------
        # Sharpen (uses 'factor' from config as intensity/stack)
        # ---------------------------
        elif filter_name == "sharpen":
            # Use 'factor' from the config to define the strength/number of times to apply the sharpen filter
            strength = int(options.get("factor", 1.0))
            # OPTIMIZATION: Clamp strength to prevent excessive processing
            strength = min(max(1, strength), 10)  # Limit to 1-10 iterations

            result = image
            for _ in range(strength):
                result = result.filter(ImageFilter.SHARPEN)
            return result

        # ---------------------------
        # Edge Enhance (uses 'factor' from config as intensity/stack)
        # ---------------------------
        elif filter_name == "edge_enhance":
            # Use 'factor' from the config to define the strength/number of times to apply the edge enhance filter
            strength = int(options.get("factor", 1.0))
            # OPTIMIZATION: Clamp strength to prevent excessive processing
            strength = min(max(1, strength), 10)  # Limit to 1-10 iterations

            result = image
            for _ in range(strength):
                result = result.filter(ImageFilter.EDGE_ENHANCE)
            return result

        # ---------------------------
        # Unknown filter
        # ---------------------------
        else:
            raise ValueError(f"Unknown filter: {filter_name}")


class SubtitleEditor(ImageEditor):
    """
    Subtitle / text overlay editor. (Implementation remains unchanged from your provided code)
    """

    # Map logical font names to candidate filenames you might find on typical OSes.
    COMMON_FONTS = {
        "arial": ["arial.ttf", "Arial.ttf", "Arial Unicode.ttf"],
        "times": ["times.ttf", "Times New Roman.ttf", "Times.ttf"],
        "courier": ["cour.ttf", "Courier New.ttf", "Courier.ttf"],
        "calibri": ["calibri.ttf", "Calibri.ttf"],
        "tahoma": ["tahoma.ttf", "Tahoma.ttf"],
        "verdana": ["verdana.ttf", "Verdana.ttf"],
        "georgia": ["georgia.ttf", "Georgia.ttf"],
        "impact": ["impact.ttf", "Impact.ttf"],
        "helvetica": ["Helvetica.ttf", "Helvetica.ttc"],
        "comic_sans": ["comic.ttf", "Comic Sans MS.ttf", "ComicSansMS.ttf"],
        "trebuchet": ["trebuc.ttf", "Trebuchet MS.ttf", "TrebuchetMS.ttf"],
    }

    STYLE_SUFFIXES = {
        "bold": ["bd", "b", "bold"],
        "italic": ["i", "it", "italic"],
        "normal": [""]
    }

    def __init__(self):
        pass

    def edit(self, image: Image.Image, **options) -> Image.Image:
        """... (Unchanged implementation) ..."""
        text = options.get("text", "")
        if text is None:
            text = ""

        base = image.convert("RGBA")
        W, H = base.size

        box = options.get("box", None)
        position = options.get("position", "bottom")
        font_name = options.get("font_name", "arial")
        style = options.get("style", "normal")
        font_size = options.get("font_size", 32)
        font_color = options.get("font_color", (255, 255, 255))
        rect = options.get("rect", False)
        rect_color = options.get("rect_color", (0, 0, 0, 160))
        rect_padding = options.get("rect_padding", 10)
        stroke_width = options.get("stroke_width", 2)
        stroke_color = options.get("stroke_color", (0, 0, 0))
        shadow = options.get("shadow", False)
        shadow_offset = options.get("shadow_offset", (2, 2))
        shadow_color = options.get("shadow_color", (0, 0, 0, 120))
        align = options.get("align", "center")
        max_lines = options.get("max_lines", None)

        if box is None:
            default_h = int(H * 0.20)
            if position == "top":
                box = (0, 0, W, default_h)
            elif position == "center":
                box = (0, (H - default_h) // 2, W, default_h)
            elif position == "top-left":
                box = (int(W * 0.05), int(H * 0.05), int(W * 0.4), int(H * 0.15))
            elif position == "top-right":
                box = (int(W * 0.55), int(H * 0.05), int(W * 0.4), int(H * 0.15))
            elif position == "bottom-left":
                box = (int(W * 0.05), int(H * 0.80), int(W * 0.4), int(H * 0.15))
            elif position == "bottom-right":
                box = (int(W * 0.55), int(H * 0.80), int(W * 0.4), int(H * 0.15))
            else:
                box = (0, H - default_h, W, default_h)

        x, y, w, h = self._normalize_box(box, W, H)
        font = self._load_font(font_name, style, font_size)
        canvas = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas, "RGBA")
        lines = self._wrap_text(text, font, draw, w)

        if max_lines and isinstance(max_lines, int):
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                if lines:
                    lines[-1] = (lines[-1].rstrip() + "…")

        try:
            ascent, descent = font.getmetrics()
            line_height = ascent + descent + int(font_size * 0.2)
        except Exception:
            line_height = font_size + 8

        text_block_height = line_height * len(lines)
        text_y = y + max(0, (h - text_block_height) // 2)

        if rect:
            left = x + rect_padding
            top = text_y - rect_padding
            right = x + w - rect_padding
            bottom = text_y + text_block_height + rect_padding
            left = max(0, left)
            top = max(0, top)
            right = min(W, right)
            bottom = min(H, bottom)
            draw.rectangle([left, top, right, bottom], fill=rect_color)

        for ln in lines:
            text_w = draw.textlength(ln, font=font)
            if align == "left":
                text_x = x + 0
            elif align == "right":
                text_x = x + w - text_w
            else:  # center
                text_x = x + (w - text_w) // 2

            if shadow:
                sx = text_x + shadow_offset[0]
                sy = text_y + shadow_offset[1]
                draw.text((sx, sy), ln, font=font, fill=shadow_color,
                          stroke_width=0)

            draw.text(
                (text_x, text_y),
                ln,
                font=font,
                fill=font_color,
                stroke_width=stroke_width,
                stroke_fill=stroke_color
            )
            text_y += line_height

        result = Image.alpha_composite(base, canvas)
        return result

    # -------------------------
    # Helpers (Unchanged implementation)
    # -------------------------
    def _normalize_box(self, box, W, H):
        """..."""
        if len(box) != 4:
            raise ValueError("box must be 4-tuple (x,y,w,h)")

        a, b, c, d = box
        if (0 <= c <= W) and (0 <= d <= H) and (c > a) and (d > b):
            x = int(a)
            y = int(b)
            w = int(c - a)
            h = int(d - b)
            return x, y, w, h

        x = int(a)
        y = int(b)
        w = int(c)
        h = int(d)
        return x, y, w, h

    def _load_font(self, font_name: str, style: str, size: int):
        """..."""
        base_key = font_name.lower()
        candidates = []

        suffixes = self.STYLE_SUFFIXES.get(style.lower(), [""])
        if base_key in self.COMMON_FONTS:
            for base_candidate in self.COMMON_FONTS[base_key]:
                name_no_ext, ext = os.path.splitext(base_candidate)
                for suff in suffixes:
                    if suff:
                        candidates.append(f"{name_no_ext}{suff}{ext}")
                        candidates.append(f"{name_no_ext}-{suff}{ext}")
                    candidates.append(base_candidate)
        else:
            candidates.append(f"{font_name}.ttf")
            candidates.append(f"{font_name}.otf")

        for fallback in ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "arial.ttf"]:
            candidates.append(fallback)

        for c in candidates:
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue

        return ImageFont.load_default()

    def _wrap_text(self, text, font, draw, max_width):
        """..."""
        text = text.replace("\r", "")
        words = text.split()
        if not words:
            return [""]

        lines = []
        line = words[0]
        for word in words[1:]:
            test = f"{line} {word}"
            if draw.textlength(test, font=font) <= max_width:
                line = test
            else:
                lines.append(line)
                line = word
        lines.append(line)
        return lines


class WatermarkEditor(ImageEditor):
    """
    Add a PNG watermark to an image. (Implementation remains unchanged from your provided code)
    """

    def edit(self, image: Image.Image, **options) -> Image.Image:
        watermark_path = options.get("watermark")
        if not watermark_path:
            raise ValueError("WatermarkEditor requires 'watermark' path in options.")

        watermark = Image.open(watermark_path)

        if not watermark_path.lower().endswith(".png"):
            raise ValueError("Watermark must be a PNG file with transparency.")

        image = image.convert("RGBA")
        watermark = watermark.convert("RGBA")

        opacity = options.get("opacity", 0.5)
        watermark = self._apply_opacity(watermark, opacity)

        max_width = options.get("max_width")
        max_height = options.get("max_height")
        if max_width or max_height:
            watermark = self._resize_watermark(watermark, max_width, max_height)

        position = options.get("position", "bottom-right")
        if isinstance(position, tuple):
            x, y = position
        else:
            x, y = self._preset_position(position, image, watermark)

        result = image.copy()
        result.alpha_composite(watermark, (x, y))
        return result

    def _apply_opacity(self, watermark: Image.Image, opacity: float):
        if opacity >= 1:
            return watermark
        if opacity <= 0:
            opacity = 0

        alpha = watermark.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        watermark.putalpha(alpha)
        return watermark

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

        # Handle both old and new Pillow API versions
        try:
            LANCZOS = Image.Resampling.LANCZOS
        except AttributeError:
            LANCZOS = Image.LANCZOS

        return watermark.resize((w, h), LANCZOS)

    def _preset_position(self, name, base, wm):
        bw, bh = base.size
        ww, wh = wm.size

        margin = 20

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
            return (0, 0)

        else:
            raise ValueError(f"Unknown preset position '{name}'. Use tuple (x, y) for custom position.")


class OverlayEditor(ImageEditor):
    """
    Add a PNG overlay/logo to an image with custom positioning, scaling, and opacity.
    Supports drag-and-drop positioning with aspect-ratio locked scaling.
    """

    def edit(self, image: Image.Image, **options) -> Image.Image:
        overlay_path = options.get("overlay_path")
        if not overlay_path:
            raise ValueError("OverlayEditor requires 'overlay_path' in options.")

        # Validate PNG format
        if not overlay_path.lower().endswith(".png"):
            raise ValueError("Overlay must be a PNG file with transparency.")

        # Load overlay image - resolve to full path if needed
        try:
            # Check if it's a relative path, convert to absolute
            from django.core.files.storage import default_storage
            if default_storage.exists(overlay_path):
                overlay_path = default_storage.path(overlay_path)
            overlay = Image.open(overlay_path)
        except Exception as e:
            raise ValueError(f"Failed to load overlay image: {str(e)}")

        # Convert both images to RGBA for alpha compositing
        image = image.convert("RGBA")
        overlay = overlay.convert("RGBA")

        # Apply opacity (0.0 to 1.0)
        opacity = float(options.get("opacity", 1.0))
        overlay = self._apply_opacity(overlay, opacity)

        # Apply scaling (maintains aspect ratio)
        scale = float(options.get("scale", 1.0))
        if scale != 1.0:
            overlay = self._scale_overlay(overlay, scale)

        # Get position (image-relative pixel coordinates)
        x = int(options.get("x", 0))
        y = int(options.get("y", 0))

        # Ensure overlay stays within image bounds
        x = max(0, min(x, image.width - overlay.width))
        y = max(0, min(y, image.height - overlay.height))

        # Composite overlay onto image
        result = image.copy()
        result.alpha_composite(overlay, (x, y))

        return result

    def _apply_opacity(self, overlay: Image.Image, opacity: float):
        """Apply opacity to overlay by modifying its alpha channel."""
        if opacity >= 1.0:
            return overlay
        if opacity <= 0.0:
            # Return fully transparent overlay
            opacity = 0.0

        # Extract alpha channel and adjust brightness
        alpha = overlay.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        overlay.putalpha(alpha)
        return overlay

    def _scale_overlay(self, overlay: Image.Image, scale: float):
        """Scale overlay maintaining aspect ratio."""
        if scale <= 0:
            scale = 0.1  # Minimum scale

        w, h = overlay.size
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        # Handle both old and new Pillow API versions
        try:
            LANCZOS = Image.Resampling.LANCZOS
        except AttributeError:
            LANCZOS = Image.LANCZOS

        return overlay.resize((new_w, new_h), LANCZOS)


