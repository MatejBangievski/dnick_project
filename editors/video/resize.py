from moviepy import VideoFileClip


class VideoEditor:
    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        raise NotImplementedError

"""
Resize video to (width, height). Supports upscaling.
"""
class VideoResizeEditor(VideoEditor):
    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        width = options.get("width")
        height = options.get("height")

        if width is None or height is None:
            raise ValueError("VideoResizeEditor requires both width and height")


        return video.resized(width=width, height=height)

