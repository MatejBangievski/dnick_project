from editors.image.watermark import WatermarkEditor
from PIL import Image

img_path = "../resources/sheep.png"
img = Image.open(img_path)


# =============================
# 5️⃣ Watermark Demo
# =============================

watermark_editor = WatermarkEditor()
watermark_path = "../resources/finki_logo.png"

# --- Default watermark (bottom-right, opacity 0.5) ---
watermarked_default = watermark_editor.edit(
    img,
    watermark=watermark_path
)
watermarked_default.save("../output/image/sheep_watermark_default.png")
print("Watermark (default bottom-right, opacity 0.5) saved as output/image/sheep_watermark_default.png")

# --- Watermark with custom opacity ---
watermarked_opacity = watermark_editor.edit(
    img,
    watermark=watermark_path,
    opacity=0.2
)
watermarked_opacity.save("../output/image/sheep_watermark_opacity_02.png")
print("Watermark (opacity 0.2) saved as output/image/sheep_watermark_opacity_02.png")

# --- Watermark at top-left ---
watermarked_topleft = watermark_editor.edit(
    img,
    watermark=watermark_path,
    position="top-left"
)
watermarked_topleft.save("../output/image/sheep_watermark_topleft.png")
print("Watermark (top-left) saved as output/image/sheep_watermark_topleft.png")

# --- Watermark at center with stronger opacity ---
watermarked_center = watermark_editor.edit(
    img,
    watermark=watermark_path,
    position="center",
    opacity=0.8
)
watermarked_center.save("../output/image/sheep_watermark_center.png")
print("Watermark (center, opacity 0.8) saved as output/image/sheep_watermark_center.png")

# --- Custom absolute position ---
watermarked_custom = watermark_editor.edit(
    img,
    watermark=watermark_path,
    position=(80, 120),   # x=80, y=120
    opacity=0.6
)
watermarked_custom.save("../output/image/sheep_watermark_custom_xy.png")
print("Watermark (custom position 80,120) saved as output/image/sheep_watermark_custom_xy.png")

# --- Watermark resized to max width 150px ---
watermarked_resized = watermark_editor.edit(
    img,
    watermark=watermark_path,
    max_width=150,
    opacity=0.7
)
watermarked_resized.save("../output/image/sheep_watermark_resized.png")
print("Watermark (resized to max width 150px) saved as output/image/sheep_watermark_resized.png")
