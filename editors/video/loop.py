from moviepy import VideoFileClip, vfx
from typing import Any

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