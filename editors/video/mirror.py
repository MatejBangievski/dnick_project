from moviepy import VideoFileClip, vfx
from typing import Any


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