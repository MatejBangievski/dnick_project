from moviepy import VideoFileClip, vfx
from typing import Any


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