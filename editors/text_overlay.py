from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from editors.base import ImageEditor
import os


class SubtitleEditor(ImageEditor):
    """
    Subtitle / text overlay editor.

    edit(image, text="...", box=None, position="bottom", font_name="arial",
         style="normal", font_size=32, font_color=(255,255,255[,a]),
         rect=False, rect_color=(0,0,0,160),
         stroke_width=2, stroke_color=(0,0,0),
         shadow=False, shadow_offset=(2,2), shadow_color=(0,0,0,120),
         align="center")
    """

    # Map logical font names to candidate filenames you might find on typical OSes.
    # You can expand these paths or add absolute paths to be robust.
    COMMON_FONTS = {
        "arial":        ["arial.ttf", "Arial.ttf"],
        "times":        ["times.ttf", "Times New Roman.ttf", "Times.ttf"],
        "courier":      ["cour.ttf", "Courier New.ttf"],
        "calibri":      ["calibri.ttf", "Calibri.ttf"],
        "tahoma":       ["tahoma.ttf", "Tahoma.ttf"],
        "verdana":      ["verdana.ttf", "Verdana.ttf"],
        "georgia":      ["georgia.ttf", "Georgia.ttf"],
        "impact":       ["impact.ttf", "Impact.ttf"],
        "helvetica":    ["Helvetica.ttf"],
        # bold/italic suffixes will be appended/check for *_bd/_bold/_i/_italic candidates below
    }

    STYLE_SUFFIXES = {
        "bold": ["bd", "b", "bold"],
        "italic": ["i", "it", "italic"],
        "normal": [""]
    }

    def __init__(self):
        # Optionally you can scan system font directories here to enhance COMMON_FONTS
        pass

    # -------------------------
    # Public API (ImageEditor)
    # -------------------------
    def edit(self, image: Image.Image, **options) -> Image.Image:
        """
        Required options:
            text (str) - the text to draw (can contain newlines)

        Other options (defaults shown):
            box=None (x,y,w,h) or None -> bottom 20% default
            position='bottom' (used only when box is None): top, bottom, center, top-left, ...
            font_name='arial'
            style='normal'  # normal | bold | italic
            font_size=32
            font_color=(255,255,255) or (r,g,b,a)
            rect=False
            rect_color=(0,0,0,160)
            rect_padding=10
            stroke_width=2
            stroke_color=(0,0,0)
            shadow=False
            shadow_offset=(2,2)
            shadow_color=(0,0,0,120)
            align='center'  # left | center | right
            max_lines=None  # optional clamp on line count
        """
        text = options.get("text", "")
        if text is None:
            text = ""

        # copy image so we don't mutate caller's reference
        base = image.convert("RGBA")
        W, H = base.size

        # Extract options with defaults
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

        # Determine box (x, y, w, h)
        if box is None:
            # default: bottom 20%
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
                # 'bottom' and any unknown -> bottom
                box = (0, H - default_h, W, default_h)

        # Accept box as either (x, y, w, h) OR (x, y, right, bottom) - normalize:
        # If user passed a 4-tuple where third and fourth are <=1 (percent), treat as percentage width/height? (not necessary)
        x, y, w, h = self._normalize_box(box, W, H)

        # Load font (try style variants)
        font = self._load_font(font_name, style, font_size)

        # Prepare drawing surface
        canvas = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Wrap text to fit width w (simple greedy line wrapping)
        lines = self._wrap_text(text, font, draw, w)

        if max_lines and isinstance(max_lines, int):
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                # optionally add ellipsis
                if lines:
                    lines[-1] = (lines[-1].rstrip() + "…")

        # Compute line height using font metrics
        # safe bbox for typical characters
        try:
            ascent, descent = font.getmetrics()
            # estimate line height
            line_height = ascent + descent + int(font_size * 0.2)
        except Exception:
            # fallback
            line_height = font_size + 8

        text_block_height = line_height * len(lines)

        # Vertical placement inside box: center vertically by default
        text_y = y + max(0, (h - text_block_height) // 2)

        # If rect requested, draw rectangle behind the text
        if rect:
            left = x + rect_padding
            top = text_y - rect_padding
            right = x + w - rect_padding
            bottom = text_y + text_block_height + rect_padding
            # clamp values
            left = max(0, left)
            top = max(0, top)
            right = min(W, right)
            bottom = min(H, bottom)
            draw.rectangle([left, top, right, bottom], fill=rect_color)

        # Draw each line with optional shadow & stroke
        for ln in lines:
            # compute width of this line
            text_w = draw.textlength(ln, font=font)
            if align == "left":
                text_x = x + 0
            elif align == "right":
                text_x = x + w - text_w
            else:  # center
                text_x = x + (w - text_w) // 2

            # draw shadow first if requested
            if shadow:
                sx = text_x + shadow_offset[0]
                sy = text_y + shadow_offset[1]
                draw.text((sx, sy), ln, font=font, fill=shadow_color,
                          stroke_width=0)

            # main text (Pillow supports stroke parameters)
            draw.text(
                (text_x, text_y),
                ln,
                font=font,
                fill=font_color,
                stroke_width=stroke_width,
                stroke_fill=stroke_color
            )

            text_y += line_height

        # composite onto base
        result = Image.alpha_composite(base, canvas)
        return result

    # -------------------------
    # Helpers
    # -------------------------
    def _normalize_box(self, box, W, H):
        """
        Accepts box as either (x,y,w,h) or (left, top, right, bottom) and returns x,y,w,h
        Heuristic: if third value > W/10, treat as width, else if it's <= W treat it as right coordinate.
        Simpler: if third > W/2 or fourth > H/2 -> treat as width/height else treat as right/bottom.
        To keep it predictable, we accept (x,y,w,h) where w,h are width/height. If user wants right/bottom,
        they can pass tuple (left, top, right, bottom) and this function will convert.
        """
        if len(box) != 4:
            raise ValueError("box must be 4-tuple (x,y,w,h)")

        a, b, c, d = box
        # Heuristic: if c > W or d > H, assume c,d are right/bottom coords (not typical). We'll detect if c > a and d > b and (c <= W and d <= H)
        if (0 <= c <= W) and (0 <= d <= H) and (c > a) and (d > b):
            # treat as left, top, right, bottom => convert to width/height
            x = int(a)
            y = int(b)
            w = int(c - a)
            h = int(d - b)
            return x, y, w, h

        # otherwise treat as x,y,width,height
        x = int(a)
        y = int(b)
        w = int(c)
        h = int(d)
        return x, y, w, h

    def _load_font(self, font_name: str, style: str, size: int):
        """
        Try a few candidates for the requested font_name and style.
        style in 'normal'|'bold'|'italic'
        """
        base_key = font_name.lower()
        candidates = []

        # Try exact: font_name + style suffixes
        suffixes = self.STYLE_SUFFIXES.get(style.lower(), [""])
        # build probable file names:
        if base_key in self.COMMON_FONTS:
            for base_candidate in self.COMMON_FONTS[base_key]:
                # try style-modified filenames
                name_no_ext, ext = os.path.splitext(base_candidate)
                for suff in suffixes:
                    if suff:
                        candidates.append(f"{name_no_ext}{suff}{ext}")
                        candidates.append(f"{name_no_ext}-{suff}{ext}")
                    # also try original
                    candidates.append(base_candidate)
        else:
            # If unknown base key, try the raw name
            candidates.append(f"{font_name}.ttf")
            candidates.append(f"{font_name}.otf")

        # Also try some generic fallbacks
        for fallback in ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "arial.ttf"]:
            candidates.append(fallback)

        # Try to load candidates
        for c in candidates:
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue

        # Final fallback
        return ImageFont.load_default()

    def _wrap_text(self, text, font, draw, max_width):
        """
        Greedy wrap: splits on spaces, fits as many words per line as allowed.
        Returns list of lines.
        """
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
