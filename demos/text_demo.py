from PIL import Image
from editors.text_overlay import SubtitleEditor

img = Image.open("../resources/sheep.png")

editor = SubtitleEditor()

# 1) Default bottom subtitle
out1 = editor.edit(img, text="Default subtitle (bottom) -- stroke + shadow", rect=False, shadow=True)
out1.save("../output/sub_default.png")

# 2) Big bold centered with rectangle
out2 = editor.edit(
    img,
    text="Centered Title Example",
    position="center",
    font_name="arial",
    style="bold",
    font_size=48,
    rect=True,
    rect_color=(0,0,0,160),
    stroke_width=3,
    shadow=True
)
out2.save("../output/sub_center.png")

# 3) Custom box and color with italic
out3 = editor.edit(
    img,
    text="Custom top-left box\nMultiple lines supported",
    box=(20, 20, int(img.width*0.5), int(img.height*0.2)),
    font_name="times",
    style="italic",
    font_size=28,
    font_color=(255, 215, 0),
    rect=True,
    rect_color=(10,10,10,180),
)
out3.save("../output/sub_custom_box.png")
