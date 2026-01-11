from typing import Any
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ImageClip, vfx
from PIL import Image, ImageDraw, ImageFont
import numpy as np

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
    """
    Adds a text watermark using Pillow (No ImageMagick required).
    """

    def edit(self, video, **options):
        text = options.get("text", "Default Watermark")
        font_size = options.get("font_size", 40)
        color = options.get("color", "white")
        position = options.get("position", ("right", "bottom"))


        img = Image.new('RGBA', (video.w, video.h), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)


        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()


        draw.text((50, video.h - 100), text, fill=color, font=font)

        watermark_array = np.array(img)
        text_clip = (ImageClip(watermark_array)
                     .with_duration(video.duration)
                     .with_position((0, 0)))

        return CompositeVideoClip([video, text_clip])


class VideoImageWatermarkEditor:
    """
    Adds an image (logo) overlay to the video.
    """
    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        image_path = options.get("image_path")
        position = options.get("position", ("right", "bottom"))
        # Optional: scale the logo (e.g., 0.1 for 10% of original size)
        scale = options.get("scale", 1.0)
        # Optional: transparency (0.0 to 1.0)
        opacity = options.get("opacity", 1.0)

        if not image_path:
            raise ValueError("VideoImageWatermarkEditor requires 'image_path'")


        logo = ImageClip(image_path)
        logo = (logo
                .resized(scale)
                .with_duration(video.duration)
                .with_opacity(opacity)
                .with_position(position))

        return CompositeVideoClip([video, logo])
