from PIL import Image
from editors.resize import ResizeEditor
from editors.crop import CropEditor
from editors.rotate import RotateEditor

# Load the original image
img_path = "resources/sheep.png"
img = Image.open(img_path)

# =============================
# 1️⃣ Resize Demo
# =============================
resize_editor = ResizeEditor()
resized_img = resize_editor.edit(img, width=300, height=200)  # Resize to 300x200
resized_img.save("output/sheep_resized.png")
print("Resized image saved as output/sheep_resized.png")

# =============================
# 2️⃣ Crop Demo
# =============================
crop_editor = CropEditor()
# Crop box: left, top, right, bottom
cropped_img = crop_editor.edit(img, left=50, top=50, right=250, bottom=200)
cropped_img.save("output/sheep_cropped.png")
print("Cropped image saved as output/sheep_cropped.png")

# =============================
# 3️⃣ Rotate Demo
# =============================
rotate_editor = RotateEditor()
# Custom rotation
rotated_img = rotate_editor.edit(img, angle=45)
rotated_img.save("output/sheep_rotated_custom.png")
print("Rotated (custom 45°) image saved as output/sheep_rotated_custom.png")

# Preset rotations
rotated_90 = rotate_editor.rotate_90(img)
rotated_90.save("output/sheep_rotated_90.png")
print("Rotated 90° image saved as output/sheep_rotated_90.png")

rotated_180 = rotate_editor.rotate_180(img)
rotated_180.save("output/sheep_rotated_180.png")
print("Rotated 180° image saved as output/sheep_rotated_180.png")

rotated_270 = rotate_editor.rotate_270(img)
rotated_270.save("output/sheep_rotated_270.png")
print("Rotated 270° image saved as output/sheep_rotated_270.png")
