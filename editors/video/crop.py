from moviepy import VideoFileClip


class VideoCropEditor:
    """
    Crops the video based on pixel coordinates.
    (x1, y1) is the top-left corner.
    (x2, y2) is the bottom-right corner.
    """
    def edit(self, video: VideoFileClip, **options) -> VideoFileClip:
        x1 = options.get("x1", 0)
        y1 = options.get("y1", 0)
        x2 = options.get("x2")
        y2 = options.get("y2")

        if x2 is None or y2 is None:
            raise ValueError("VideoCropEditor requires x2 and y2 coordinates")

        return video.cropped(x1=x1, y1=y1, x2=x2, y2=y2)

