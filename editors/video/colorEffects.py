from moviepy import VideoFileClip
from moviepy import vfx


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