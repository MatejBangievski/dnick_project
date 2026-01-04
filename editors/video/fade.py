from moviepy import vfx


class VideoFadeEditor:
    def edit(self, video, **options):
        f_in = options.get("fade_in", 1.0)
        f_out = options.get("fade_out", 1.0)

        # Class-based names are usually FadeIn and FadeOut
        video = vfx.FadeIn(duration=f_in).apply(video)
        video = vfx.FadeOut(duration=f_out).apply(video)
        return video