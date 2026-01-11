from moviepy import VideoFileClip, vfx
from typing import Any


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