import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip

from editors.video.crop import VideoCropEditor
from editors.video.loop import VideoLoopEditor
from editors.video.mirror import VideoMirrorEditor
from editors.video.resize import VideoResizeEditor
from editors.video.rotate import VideoRotateEditor
from editors.video.speed import VideoSpeedEditor
from editors.video.colorEffects import *
from editors.video.fade import VideoFadeEditor
from editors.video.watermark import VideoImageWatermarkEditor, VideoWatermarkEditor


INPUT_VIDEO = "../resources/seagulls-video.mp4"
LOGO_IMAGE = "../resources/finki_logo.png"
TEST_DIR = "../output/video/tests/"
FINAL_OUT = "../output/video/seagulls_MASTER_DEMO.mp4"

if not os.path.exists(TEST_DIR):
    os.makedirs(TEST_DIR)

base_clip = VideoFileClip(INPUT_VIDEO)

resizer = VideoResizeEditor()
cropper = VideoCropEditor()
speeder = VideoSpeedEditor()
grayer = VideoGrayscaleEditor()
colorer = VideoColorEditor()
fader = VideoFadeEditor()
tinter = VideoTintEditor()
watermarker = VideoImageWatermarkEditor()
text_mark = VideoWatermarkEditor()
rotator= VideoRotateEditor()
mirrorer = VideoMirrorEditor()
looper= VideoLoopEditor()


print("--- Starting Individual Unit Tests ---")

# Test 1: Color & Contrast
print("Testing: Color/Contrast...")
colorer.edit(base_clip, intensity=1.8, contrast=0.4).write_videofile(f"{TEST_DIR}test_color.mp4")

# Test 2: Tinting (Cool Blue Look)
print("Testing: Tinting...")
tinter.edit(base_clip, r=0.8, g=1.0, b=1.3).write_videofile(f"{TEST_DIR}test_tint.mp4")

print("Testing: Grayscale...")
grayer.edit(base_clip).write_videofile(f"{TEST_DIR}test_grayscale.mp4")

# Test 3: Fading
print("Testing: Fading...")
fader.edit(base_clip, fade_in=2.0, fade_out=2.0).write_videofile(f"{TEST_DIR}test_fade.mp4")

print("Testing: Rotation (90 degrees)...")
rotator.edit(base_clip, angle=90).write_videofile(f"{TEST_DIR}test_rotate.mp4")

print("Testing: Horizontal Mirror...")
mirrorer.edit(base_clip, horizontal=True).write_videofile(f"{TEST_DIR}test_mirror.mp4")

print("Testing: Looping (2 times)...")
looper.edit(base_clip, n=2).write_videofile(f"{TEST_DIR}test_loop.mp4")

print("Testing: Text Watermark...")
text_mark.edit(
    base_clip,
    text="DNICK-FINKI",
    font_size=50,
    color="yellow"
).write_videofile(f"{TEST_DIR}test_text_watermark.mp4")


print("\n--- Processing Final Cinematic Master ---")


final = resizer.edit(base_clip, width=1280,height=720)
final = cropper.edit(final, x1=100, y1=50, x2=1180, y2=670)

final = colorer.edit(final, intensity=1.2, contrast=0.2, brightness=5)
final = tinter.edit(final, r=0.9, g=1.0, b=1.1)

final = speeder.edit(final, factor=0.9) # Slight slow-motion


final = fader.edit(final, fade_in=1.5, fade_out=1.5)

print("Adding Image Logo...")
final = watermarker.edit(final, image_path=LOGO_IMAGE, scale=0.1, opacity=0.7)

print("Adding Text Copyright...")
final = text_mark.edit(
    final,
    text="© 2026 DNICK Projects",
    font_size=30,
    color="white"
)

print("Writing Final Master File...")
final.write_videofile(FINAL_OUT, codec="libx264", audio_codec="aac")

print(f"\nDemo Complete! Files saved in: {TEST_DIR} and {FINAL_OUT}")