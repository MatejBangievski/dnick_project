"""
Generate font preview images showing "Aa" for the font carousel.
Cross-platform compatible with diagnostics.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import platform
import sys

# Platform-specific font directories
SYSTEM = platform.system()
FONT_DIRS = []

if SYSTEM == "Darwin":  # macOS
    FONT_DIRS = [
        "/Library/Fonts/",
        "/System/Library/Fonts/",
        os.path.expanduser("~/Library/Fonts/"),
    ]
elif SYSTEM == "Windows":
    FONT_DIRS = [
        "C:\\Windows\\Fonts\\",
    ]
elif SYSTEM == "Linux":
    FONT_DIRS = [
        "/usr/share/fonts/",
        "/usr/local/share/fonts/",
        os.path.expanduser("~/.fonts/"),
    ]

# Font definitions with multiple candidates for cross-platform compatibility
FONTS = {
    "Arial": ["Arial.ttf", "arial.ttf", "Arial Unicode.ttf"],
    "Times New Roman": ["Times New Roman.ttf", "times.ttf", "Times.ttf"],
    "Courier New": ["Courier New.ttf", "cour.ttf", "Courier.ttf"],
    "Calibri": ["Calibri.ttf", "calibri.ttf"],
    "Tahoma": ["Tahoma.ttf", "tahoma.ttf"],
    "Verdana": ["Verdana.ttf", "verdana.ttf"],
    "Georgia": ["Georgia.ttf", "georgia.ttf"],
    "Impact": ["Impact.ttf", "impact.ttf"],
    "Helvetica": ["Helvetica.ttf", "Helvetica.ttc"],
    "Comic Sans": ["Comic Sans MS.ttf", "comic.ttf", "ComicSansMS.ttf"],
    "Trebuchet MS": ["Trebuchet MS.ttf", "trebuc.ttf", "TrebuchetMS.ttf"],
    "Palatino": ["Palatino.ttf", "pala.ttf", "Palatino Linotype.ttf"],
    "Garamond": ["Garamond.ttf", "gara.ttf"],
    "Bookman": ["Bookman Old Style.ttf", "bookos.ttf"],
    "Century Gothic": ["Century Gothic.ttf", "gothic.ttf"],
    "Lucida": ["Lucida Sans.ttf", "Lucida Console.ttf", "lucon.ttf"],
    "Rockwell": ["Rockwell.ttf", "rock.ttf"],
    "Consolas": ["Consolas.ttf", "consola.ttf"],
    "Times": ["Times New Roman.ttf", "times.ttf", "Times.ttf"],
    "Courier": ["Courier New.ttf", "cour.ttf", "Courier.ttf"],
    "Trebuchet": ["Trebuchet MS.ttf", "trebuc.ttf", "TrebuchetMS.ttf"],
}

FALLBACKS = ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf", "arial.ttf"]
OUTPUT_DIR = "editorproject/media/font_previews"
IMAGE_SIZE = 120
FONT_SIZE = 48
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (40, 40, 40)
BORDER_COLOR = (220, 220, 220)


def find_font_file(font_candidates):
    """Search for font file in system directories and return path if found."""
    # First try without path (PIL will search system paths)
    for font_name in font_candidates:
        try:
            # Try direct name first (works on most systems)
            font = ImageFont.truetype(font_name, 12)  # Small size for testing
            return font_name, font_name
        except:
            pass

    # Then search in known directories
    for font_dir in FONT_DIRS:
        if not os.path.exists(font_dir):
            continue
        for font_name in font_candidates:
            # Search recursively in font directory
            for root, dirs, files in os.walk(font_dir):
                if font_name in files:
                    full_path = os.path.join(root, font_name)
                    try:
                        font = ImageFont.truetype(full_path, 12)
                        return full_path, font_name
                    except:
                        pass

    return None, None


def load_font(font_candidates, size, font_name_display):
    """Load font with diagnostics."""
    font_path, font_file = find_font_file(font_candidates)

    if font_path:
        try:
            font = ImageFont.truetype(font_path, size)
            print(f"  → Loaded: {font_file}")
            return font, True
        except Exception as e:
            print(f"  ⚠ Error loading {font_file}: {e}")

    # Try fallbacks
    print(f"  ⚠ Font not found, trying fallbacks...")
    for fallback in FALLBACKS:
        fallback_path, _ = find_font_file([fallback])
        if fallback_path:
            try:
                font = ImageFont.truetype(fallback_path, size)
                print(f"  → Using fallback: {fallback}")
                return font, False
            except:
                pass

    print(f"  ✗ Using default font (bitmap)")
    return ImageFont.load_default(), False


def generate_font_preview(font_name, font_candidates, output_path):
    """Generate preview image with proper font scaling."""
    img = Image.new('RGB', (IMAGE_SIZE, IMAGE_SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, IMAGE_SIZE - 1, IMAGE_SIZE - 1], outline=BORDER_COLOR, width=2)

    font, success = load_font(font_candidates, FONT_SIZE, font_name)
    text = "Aa"

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    x = (IMAGE_SIZE - text_width) // 2
    y = (IMAGE_SIZE - text_height) // 2 - 5

    # Draw the text
    draw.text((x, y), text, fill=TEXT_COLOR, font=font)

    # Save
    img.save(output_path, 'PNG', optimize=True)

    return success


def main():
    """Generate all font preview images with diagnostics."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n" + "=" * 70)
    print(f"Font Preview Generator - {SYSTEM}")
    print("=" * 70)
    print(f"Output: {OUTPUT_DIR}")
    print(f"Image Size: {IMAGE_SIZE}x{IMAGE_SIZE}, Font Size: {FONT_SIZE}pt\n")

    success_count = 0
    fallback_count = 0

    for font_name, font_candidates in FONTS.items():
        safe_name = font_name.lower().replace(" ", "_")
        output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.png")

        print(f"📝 {font_name}:")
        try:
            success = generate_font_preview(font_name, font_candidates, output_path)
            if success:
                success_count += 1
                print(f"   ✅ {output_path}\n")
            else:
                fallback_count += 1
                print(f"   ⚠️  {output_path} (using fallback font)\n")
        except Exception as e:
            print(f"   ✗ Failed: {e}\n")

    print("=" * 70)
    print(f"✅ Successfully generated: {success_count}/{len(FONTS)} fonts")
    if fallback_count > 0:
        print(f"⚠️  Using fallback fonts: {fallback_count}/{len(FONTS)}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
