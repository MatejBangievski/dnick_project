import os
import platform
from typing import Any

from django.core.files.storage import default_storage
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ImageClip, vfx
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from django.conf import settings


def make_even(val):
    return int(val) if int(val) % 2 == 0 else int(val) - 1

class VideoCropEditor:
    """
    Crops the video based on pixel coordinates and ensures
    the resulting dimensions are even numbers for MP4 encoding.
    """

    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        x1 = int(options.get("x1", 0))
        y1 = int(options.get("y1", 0))
        x2 = int(options.get("x2", video.w))
        y2 = int(options.get("y2", video.h))

        requested_w = x2 - x1
        requested_h = y2 - y1

        safe_x2 = x1 + make_even(requested_w)
        safe_y2 = y1 + make_even(requested_h)

        return video.cropped(x1=x1, y1=y1, x2=safe_x2, y2=safe_y2)

class VideoEditor:
    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        raise NotImplementedError

"""
Resize video to (width, height). Supports upscaling.
"""
class VideoResizeEditor(VideoEditor):
    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        width = make_even(options.get("width"))
        height = make_even(options.get("height"))

        if width is None or height is None:
            raise ValueError("VideoResizeEditor requires both width and height")


        return video.resized(width=width, height=height)




class VideoRotateEditor:
    """
    Rotates the video by a given angle (in degrees).
    """

    def edit(self, video: VideoFileClip, **options: Any) -> VideoFileClip:
        angle = float(options.get("angle", 0))

        if angle == 0:
            return video

        # v2.2.1 Class-based Rotate
        try:
            return vfx.Rotate(angle=angle).apply(video)
        except AttributeError:
            return video.rotated(angle)



class VideoMirrorEditor:
    """
    Flips the video horizontally (MirrorX) or vertically (MirrorY).
    """

    def edit(self, video: VideoFileClip, **options: Any) -> VideoFileClip:
        horizontal = options.get("horizontal", False)
        vertical = options.get("vertical", False)

        if horizontal:
            try:
                video = vfx.MirrorX().apply(video)
            except AttributeError:
                video = vfx.mirror_x(video)

        if vertical:
            try:
                video = vfx.MirrorY().apply(video)
            except AttributeError:
                video = vfx.mirror_y(video)

        return video


class VideoLoopEditor:
    """
    Loops the video clip.
    n: Number of times to loop (e.g., n=2 plays the video twice).
    duration: Loops until the video reaches a specific total duration.
    """
    def edit(self, video: VideoFileClip, **options: Any) -> VideoFileClip:
        n_times = options.get("n")
        target_duration = options.get("duration")

        try:
            return vfx.Loop(n=n_times, duration=target_duration).apply(video)
        except AttributeError:
            return video.loop(n=n_times, duration=target_duration)


class VideoGrayscaleEditor:
    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        return vfx.BlackAndWhite().apply(video)


class VideoColorEditor:
    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        intensity = options.get("intensity", 1.0)
        contrast = options.get("contrast", 0.0)
        brightness = options.get("brightness", 0.0)


        video = vfx.MultiplyColor(factor=intensity).apply(video)

        video = vfx.LumContrast(lum=brightness, contrast=contrast).apply(video)

        return video


class VideoPaintingEditor:
    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        return vfx.Painting(saturation=1.5, black=0.05).apply(video)


class VideoTintEditor:
    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        r = options.get("r", 1.0)
        g = options.get("g", 1.0)
        b = options.get("b", 1.0)

        return vfx.MultiplyColor(factor=[r, g, b]).apply(video)

# Example Usage for a "Sepia/Warm" look:
# tint_editor.edit(video, r=1.2, g=1.0, b=0.8)


class VideoSpeedEditor:
    """
    Adjusts the playback speed of the video.
    """

    def edit(self, video: VideoFileClip, **options: Any) -> VideoFileClip:
        factor = float(options.get("factor", 1.0))

        if factor == 1.0:
            return video

        try:
            return vfx.MultiplySpeed(factor=factor).apply(video)
        except AttributeError:
            return video.multiply_speed(factor)


class VideoFadeEditor:
    def edit(self, video, **options):
        f_in = options.get("fade_in", 1.0)
        f_out = options.get("fade_out", 1.0)

        # Class-based names are usually FadeIn and FadeOut
        video = vfx.FadeIn(duration=f_in).apply(video)
        video = vfx.FadeOut(duration=f_out).apply(video)
        return video


class VideoWatermarkEditor:
    COMMON_FONTS = {
        "arial": ["arial.ttf", "Arial.ttf", "Arial Unicode.ttf"],
        "times_new_roman": ["times.ttf", "Times New Roman.ttf", "Times.ttf"],
        "courier_new": ["cour.ttf", "Courier New.ttf", "Courier.ttf"],
        "impact": ["impact.ttf", "Impact.ttf"],
        "comic_sans_ms": ["comic.ttf", "Comic Sans MS.ttf", "ComicSansMS.ttf"],
        "verdana": ["verdana.ttf", "Verdana.ttf"],
        "georgia": ["georgia.ttf", "Georgia.ttf"],
        "tahoma": ["tahoma.ttf", "Tahoma.ttf"],
        "trebuchet_ms": ["trebuc.ttf", "Trebuchet MS.ttf", "TrebuchetMS.ttf"],
    }

    # Added style support from SubtitleEditor
    STYLE_SUFFIXES = {
        "bold": ["bd", "b", "bold"],
        "italic": ["i", "it", "italic"],
        "normal": [""]
    }

    def edit(self, video, **options):
        text = str(options.get("text", "")).strip()
        if not text or text.lower() == "none":
            return video

        font_name = options.get("font_name", "arial").lower()
        font_size = self._safe_int(options.get("font_size"), 40)
        color = options.get("color", "#FFFFFF")
        stroke_width = self._safe_int(options.get("stroke_width"), 0)
        has_rect = options.get("rect")
        if isinstance(has_rect, str):
            has_rect = has_rect.lower() == 'true'

        box_coords = options.get("box", [0, 0, 100, 100])

        overlay = Image.new('RGBA', (video.w, video.h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 2. Using the improved font loader
        font = self._load_font(font_name, "normal", font_size)

        x, y, w, h = self._normalize_box(box_coords, video.w, video.h)
        lines = self._wrap_text(text, font, draw, w)

        bbox = font.getbbox("Ay")
        actual_font_height = bbox[3] - bbox[1]
        line_height = actual_font_height + int(font_size * 0.1)
        total_text_height = line_height * len(lines)
        start_y = y + (h - total_text_height) // 2

        if has_rect:
            padding = 10
            draw.rectangle([x, start_y - padding, x + w, start_y + total_text_height + padding], fill=(0, 0, 0, 128))

        current_y = start_y
        for line in lines:
            text_w = draw.textlength(line, font=font)
            text_x = x + (w - text_w) // 2
            draw.text((text_x, current_y), line, font=font, fill=color, stroke_width=stroke_width, stroke_fill="black")
            current_y += line_height

        watermark_array = np.array(overlay)
        text_clip = (ImageClip(watermark_array)
                     .with_duration(video.duration)
                     .with_position((0, 0)))

        return CompositeVideoClip([video, text_clip])

    def _load_font(self, font_name: str, style: str, size: int):
        """Replaced with the multi-candidate search logic from SubtitleEditor"""
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

        # System paths for deep search
        import platform
        system_dirs = []
        if platform.system() == "Windows":
            system_dirs = [os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')]
        elif platform.system() == "Linux":
            system_dirs = ["/usr/share/fonts/", "/usr/local/share/fonts/"]

        # candidates directly first
        for c in candidates:
            try:
                return ImageFont.truetype(c, size)
            except:
                continue

        # Recursive system search if direct load fails
        for d in system_dirs:
            if not os.path.exists(d): continue
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower() in [c.lower() for c in candidates]:
                        try:
                            return ImageFont.truetype(os.path.join(root, f), size)
                        except:
                            continue

        return ImageFont.load_default()

    def _safe_int(self, val, default=0):
        if val is None or str(val).strip() == "": return default
        try: return int(float(val))
        except: return default

    def _normalize_box(self, box, W, H):
        try:
            a, b, c, d = [int(float(v)) for v in box]
            if c > a and d > b: return a, b, c - a, d - b
            return a, b, c, d
        except: return 50, 50, 300, 100

    def _wrap_text(self, text, font, draw, max_width):
        words = text.split()
        if not words: return [""]
        lines, line = [], words[0]
        for word in words[1:]:
            if draw.textlength(f"{line} {word}", font=font) <= max_width:
                line += f" {word}"
            else:
                lines.append(line)
                line = word
        lines.append(line)
        return lines



class VideoImageWatermarkEditor:
    """
    Adds an image (logo) overlay to the video using either
    fixed presets or specific bounding box coordinates.
    """

    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        # 1. Get the image source
        image_source = options.get("overlay_path") or options.get("watermark_file") or options.get("image_path")

        # 2. Get positioning data
        box = options.get("box")
        position_preset = options.get("position_presets", "bottom-right")



        opacity = float(options.get("opacity", 1.0))

        if not image_source:
            raise ValueError("Image Watermark requires a logo file.")

        try:
            absolute_logo_path = default_storage.path(image_source)
        except Exception:
            absolute_logo_path = os.path.join(settings.MEDIA_ROOT, image_source)

        if not os.path.exists(absolute_logo_path):
            raise FileNotFoundError(f"Worker cannot find logo at: {absolute_logo_path}")

        # Load the logo
        logo = ImageClip(absolute_logo_path)

        # 3. Handle Sizing and Positioning
        if box:
            x1, y1, x2, y2 = box
            width = x2 - x1
            height = y2 - y1

            logo = (logo
                    .resized(width=width, height=height)
                    .with_position((x1, y1)))
        else:
            scale = float(options.get("scale", 1.0))
            logo = (logo
                    .resized(scale)
                    .with_position(self._parse_position(position_preset)))

        logo = (logo
                .with_duration(video.duration)
                .with_opacity(opacity))

        return CompositeVideoClip([video, logo])

    def _parse_position(self, preset):
        """Maps frontend button-group values to MoviePy position tuples."""
        mapping = {
            "top-left": ("left", "top"),
            "top-right": ("right", "top"),
            "bottom-left": ("left", "bottom"),
            "bottom-right": ("right", "bottom"),
            "center": ("center", "center"),
        }
        return mapping.get(preset, ("right", "bottom"))