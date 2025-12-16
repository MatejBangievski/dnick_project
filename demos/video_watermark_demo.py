from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

# =============================
# 🎥 Video Watermark Demo
# =============================

video_path = "../resources/seagulls-video.mp4"
watermark_path = "../resources/finki_logo.png"

# Вчитај видео
video = VideoFileClip(video_path)

# Вчитај watermark како ImageClip
watermark = ImageClip(watermark_path)

# --- Default watermark (bottom-right, opacity 0.5) ---
watermark_default = watermark.set_duration(video.duration).set_opacity(0.5)
watermark_default = watermark_default.set_position(("right", "bottom"))

video_with_watermark_default = CompositeVideoClip([video, watermark_default])
video_with_watermark_default.write_videofile("../output/video/video_watermark_default.mp4", codec="libx264")
print("Video watermark (default bottom-right, opacity 0.5) saved as output/video_watermark_default.mp4")

# --- Watermark at top-left with custom opacity ---
watermark_topleft = watermark.set_duration(video.duration).set_opacity(0.3)
watermark_topleft = watermark_topleft.set_position(("left", "top"))

video_with_watermark_topleft = CompositeVideoClip([video, watermark_topleft])
video_with_watermark_topleft.write_videofile("../output/video/video_watermark_topleft.mp4", codec="libx264")
print("Video watermark (top-left, opacity 0.3) saved as output/video/video_watermark_topleft.mp4")

# --- Watermark at center with stronger opacity ---
watermark_center = watermark.set_duration(video.duration).set_opacity(0.8)
watermark_center = watermark_center.set_position("center")

video_with_watermark_center = CompositeVideoClip([video, watermark_center])
video_with_watermark_center.write_videofile("../output/video/video_watermark_center.mp4", codec="libx264")
print("Video watermark (center, opacity 0.8) saved as output/video/video_watermark_center.mp4")

# --- Custom absolute position (x=80, y=120) ---
watermark_custom = watermark.set_duration(video.duration).set_opacity(0.6)
watermark_custom = watermark_custom.set_position((80, 120))

video_with_watermark_custom = CompositeVideoClip([video, watermark_custom])
video_with_watermark_custom.write_videofile("../output/video/video_watermark_custom_xy.mp4", codec="libx264")
print("Video watermark (custom position 80,120) saved as output/video/video_watermark_custom_xy.mp4")

# --- Watermark resized to max width 150px ---
watermark_resized = watermark.resize(width=150).set_duration(video.duration).set_opacity(0.7)
watermark_resized = watermark_resized.set_position(("right", "bottom"))

video_with_watermark_resized = CompositeVideoClip([video, watermark_resized])
video_with_watermark_resized.write_videofile("../output/video/video_watermark_resized.mp4", codec="libx264")
print("Video watermark (resized to max width 150px) saved as output/video/video_watermark_resized.mp4")
