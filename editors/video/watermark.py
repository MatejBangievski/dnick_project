from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np

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

