from PIL import Image
from editors.resize import ResizeEditor
from editors.crop import CropEditor
from editors.rotate import RotateEditor
from editors.filter import FilterEditor

# Load the original image
img_path = "../resources/sheep.png"
img = Image.open(img_path)

# =============================
# 1️⃣ Resize Demo
# =============================
resize_editor = ResizeEditor()
resized_img = resize_editor.edit(img, width=300, height=200)
resized_img.save("../output/sheep_resized.png")
print("Resized image saved as output/sheep_resized.png")

# =============================
# 2️⃣ Crop Demo
# =============================
crop_editor = CropEditor()
cropped_img = crop_editor.edit(img, left=50, top=50, right=250, bottom=200)
cropped_img.save("../output/sheep_cropped.png")
print("Cropped image saved as output/sheep_cropped.png")

# =============================
# 3️⃣ Rotate Demo
# =============================
rotate_editor = RotateEditor()

rotated_img = rotate_editor.edit(img, angle=45)
rotated_img.save("../output/sheep_rotated_custom.png")
print("Rotated (custom 45°) image saved as output/sheep_rotated_custom.png")

rotate_editor.rotate_90(img).save("../output/sheep_rotated_90.png")
print("Rotated 90° image saved as output/sheep_rotated_90.png")

rotate_editor.rotate_180(img).save("../output/sheep_rotated_180.png")
print("Rotated 180° image saved as output/sheep_rotated_180.png")

rotate_editor.rotate_270(img).save("../output/sheep_rotated_270.png")
print("Rotated 270° image saved as output/sheep_rotated_270.png")

# =============================
# 4️⃣ Filter Demo
# =============================

filter_editor = FilterEditor()

# --- Grayscale ---
grayscale_img = filter_editor.edit(img, filter="grayscale")
grayscale_img.save("../output/sheep_grayscale.png")
print("Grayscale saved as output/sheep_grayscale.png")

# --- Invert ---
invert_img = filter_editor.edit(img, filter="invert")
invert_img.save("../output/sheep_invert.png")
print("Invert saved as output/sheep_invert.png")

# --- Sepia (default intensity) ---
sepia_default = filter_editor.edit(img, filter="sepia")
sepia_default.save("../output/sheep_sepia_default.png")
print("Sepia (default) saved as output/sheep_sepia_default.png")

# --- Sepia (custom intensity) ---
sepia_custom = filter_editor.edit(img, filter="sepia", intensity=0.4)
sepia_custom.save("../output/sheep_sepia_custom.png")
print("Sepia (custom intensity 0.4) saved as output/sheep_sepia_custom.png")

# --- Brighten (default 1.5) ---
bright_default = filter_editor.edit(img, filter="brighten")
bright_default.save("../output/sheep_brighten_default.png")
print("Brighten (default) saved as output/sheep_brighten_default.png")

# --- Brighten (custom) ---
bright_custom = filter_editor.edit(img, filter="brighten", factor=2.2)
bright_custom.save("../output/sheep_brighten_custom.png")
print("Brighten (custom factor 2.2) saved as output/sheep_brighten_custom.png")

# --- Contrast (default) ---
contrast_default = filter_editor.edit(img, filter="contrast")
contrast_default.save("../output/sheep_contrast_default.png")
print("Contrast (default) saved as output/sheep_contrast_default.png")

# --- Contrast (custom) ---
contrast_custom = filter_editor.edit(img, filter="contrast", factor=2.0)
contrast_custom.save("../output/sheep_contrast_custom.png")
print("Contrast (custom factor 2.0) saved as output/sheep_contrast_custom.png")

# --- Blur (default radius 2) ---
blur_default = filter_editor.edit(img, filter="blur")
blur_default.save("../output/sheep_blur_default.png")
print("Blur (default radius 2) saved as output/sheep_blur_default.png")

# --- Blur (custom radius) ---
blur_custom = filter_editor.edit(img, filter="blur", radius=6)
blur_custom.save("../output/sheep_blur_custom.png")
print("Blur (custom radius 6) saved as output/sheep_blur_custom.png")

# --- Sharpen (default) ---
sharpen_default = filter_editor.edit(img, filter="sharpen")
sharpen_default.save("../output/sheep_sharpen_default.png")
print("Sharpen (default) saved as output/sheep_sharpen_default.png")

# --- Sharpen (stronger) ---
sharpen_custom = filter_editor.edit(img, filter="sharpen", strength=3)
sharpen_custom.save("../output/sheep_sharpen_custom.png")
print("Sharpen (strength 3) saved as output/sheep_sharpen_custom.png")

# --- Edge Enhance (default) ---
edge_default = filter_editor.edit(img, filter="edge_enhance")
edge_default.save("../output/sheep_edge_default.png")
print("Edge Enhance (default) saved as output/sheep_edge_default.png")

# --- Edge Enhance (strong) ---
edge_custom = filter_editor.edit(img, filter="edge_enhance", strength=3)
edge_custom.save("../output/sheep_edge_custom.png")
print("Edge Enhance (strength 3) saved as output/sheep_edge_custom.png")