# imageditor/config.py
from .editors.editors import CropEditor, FilterEditor, ResizeEditor, RotateEditor, SubtitleEditor, WatermarkEditor, OverlayEditor
from .editors.videoEditors import *
# Define all tools and their configuration for the UI and backend logic
# This structure makes the app scalable for future tools.

# UI element types: 'slider', 'number', 'text', 'select', 'checkbox', 'button', 'color'
EDITOR_TOOLS = {
    "filter": {
        # ... (Filter tool config remains unchanged)
        "name": "Filters & Enhancement",
        "editor_class": FilterEditor,
        "options": [
            {
                "id": "filter",
                "label": "Select Filter",
                "type": "select",
                "default": "none",
                "choices": [
                    {"value": "none", "label": "None"},
                    {"value": "grayscale", "label": "Grayscale"},
                    {"value": "invert", "label": "Invert Colors"},
                    {"value": "sepia", "label": "Sepia Tone"},
                    {"value": "brighten", "label": "Brightness"},
                    {"value": "contrast", "label": "Contrast"},
                    {"value": "blur", "label": "Blur (Radius)"},
                    {"value": "sharpen", "label": "Sharpen (Strength)"},
                    {"value": "edge_enhance", "label": "Edge Enhance"},
                ]
            },
            {
                "id": "factor",
                "label": "Factor/Strength",
                "type": "slider",
                "min": 0.0,
                "max": 5.0,
                "step": 0.1,
                "default": 1.0,
                "applies_to": ["brighten", "contrast", "sepia"]
            },
            {
                "id": "radius",
                "label": "Blur Radius",
                "type": "slider",
                "min": 0,
                "max": 10,
                "step": 1,
                "default": 0,
                "applies_to": ["blur"]
            },
        ]
    },
    "crop": {
        "name": "Crop & Aspect Ratio",
        "editor_class": CropEditor,
        "options": [
            {
                "id": "aspect_ratio_presets",
                "label": "Aspect Ratio Presets",
                "type": "aspect-ratio-group",
                "buttons": [
                    {"value": "free", "label": "Free"},
                    {"value": "1:1", "label": "1:1"},
                    {"value": "4:3", "label": "4:3"},
                    {"value": "3:2", "label": "3:2"},
                    {"value": "16:9", "label": "16:9"},
                    {"value": "9:16", "label": "9:16"},
                    {"value": "2:3", "label": "2:3"},
                ]
            },
        ]
    },
    "rotate": {
        "name": "Rotate",
        "editor_class": RotateEditor,
        "options": [
            # NEW: Preset buttons for quick rotation
            {
                "id": "presets",
                "label": "Quick Rotation Presets",
                "type": "button-group",  # Custom type for button group
                "buttons": [
                    {"value": 90, "label": "90°"},
                    {"value": 180, "label": "180°"},
                    {"value": 270, "label": "270°"},
                ]
            },
            # Existing Angle slider
            {
                "id": "angle",
                "label": "Angle (°)",
                "type": "slider",
                "min": 0,
                "max": 360,
                "step": 1,
                "default": 0,
            }
        ]
    },
    "resize": {
        # ... (Resize tool config remains unchanged)
        "name": "Resize",
        "editor_class": ResizeEditor,
        "options": [
            {
                "id": "width",
                "label": "New Width",
                "type": "number",
                "min": 1,
                "default": 0,
            },
            {
                "id": "height",
                "label": "New Height",
                "type": "number",
                "min": 1,
                "default": 0,
            },
        ]
    },
    "subtitle": {
        # ... (Subtitle tool config remains unchanged)
        "name": "Add Text/Subtitle",
        "editor_class": SubtitleEditor,
        "options": [
            {
                "id": "text",
                "label": "Text",
                "type": "text",
                "default": "",
            },
            # ADD THIS NEW OPTION:
            {
                "id": "font_name",
                "label": "Font Family",
                "type": "font-carousel",
                "default": "arial",
                "fonts": [
                    {"value": "arial", "label": "Arial"},
                    {"value": "times", "label": "Times New Roman"},
                    {"value": "georgia", "label": "Georgia"},
                    {"value": "courier", "label": "Courier New"},
                    {"value": "verdana", "label": "Verdana"},
                    {"value": "tahoma", "label": "Tahoma"},
                    {"value": "trebuchet", "label": "Trebuchet MS"},
                    {"value": "impact", "label": "Impact"},
                    {"value": "comic_sans", "label": "Comic Sans"},
                ]
            },
            {
                "id": "font_size",
                "label": "Font Size",
                "type": "number",
                "min": 10,
                "max": 100,
                "default": 32,
            },
            {
                "id": "font_color",
                "label": "Font Color",
                "type": "color",
                "default": "#FFFFFF",
            },
            {
                "id": "stroke_width",
                "label": "Outline Width",
                "type": "number",
                "min": 0,
                "max": 10,
                "default": 0,
            },
            {
                "id": "rect",
                "label": "Background Box",
                "type": "checkbox",
                "default": False,
            },
        ]
    },
    "overlay": {
        "name": "Add PNG Overlay/Logo",
        "editor_class": OverlayEditor,
        "options": [
            {
                "id": "overlay_file",
                "label": "Upload PNG Image",
                "type": "file",
                "accept": ".png",
                "default": None,
            },
            {
                "id": "opacity",
                "label": "Transparency/Opacity",
                "type": "slider",
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "default": 1.0,
            },
            {
                "id": "opacity_presets",
                "label": "Quick Opacity Presets",
                "type": "opacity-button-group",
                "buttons": [
                    {"value": 0.25, "label": "25%"},
                    {"value": 0.5, "label": "50%"},
                    {"value": 0.75, "label": "75%"},
                    {"value": 1.0, "label": "100%"},
                ]
            },
            {
                "id": "position_presets",
                "label": "Position Presets",
                "type": "position-button-group",
                "buttons": [
                    {"value": "center", "label": "Center"},
                    {"value": "top-left", "label": "Top Left"},
                    {"value": "top-right", "label": "Top Right"},
                    {"value": "bottom-left", "label": "Bottom Left"},
                    {"value": "bottom-right", "label": "Bottom Right"},
                ]
            },
            {
                "id": "x",
                "label": "X Position",
                "type": "hidden",
                "default": 0,
            },
            {
                "id": "y",
                "label": "Y Position",
                "type": "hidden",
                "default": 0,
            },
            {
                "id": "scale",
                "label": "Scale",
                "type": "hidden",
                "default": 1.0,
            },
            {
                "id": "overlay_path",
                "label": "Overlay Path",
                "type": "hidden",
                "default": "",
            },
        ]
    },
    "video_speed": {
        "name": "Video Speed",
        "editor_class": VideoSpeedEditor,
        "options": [
            {
                "id": "factor",
                "label": "Speed Factor (0.5x - 2.0x)",
                "type": "slider",
                "min": 0.1,
                "max": 3.0,
                "step": 0.1,
                "default": 1.0,
            },
            {
                "id": "factor",
                "label": "Quick Presets",
                "type": "button-group",
                "buttons": [
                    {"value": 0.5, "label": "Slow (0.5x)"},
                    {"value": 1.0, "label": "Normal (1x)"},
                    {"value": 2.0, "label": "Fast (2x)"},
                ]
            }
        ]
    },
    "video_mirror": {
        "name": "Video Mirror",
        "editor_class": VideoMirrorEditor,
        "options": [
            {
                "id": "horizontal",
                "label": "Flip Horizontal",
                "type": "checkbox",
                "default": False,
            },
            {
                "id": "vertical",
                "label": "Flip Vertical",
                "type": "checkbox",
                "default": False,
            }
        ]
    },
    "video_loop": {
        "name": "Video Loop",
        "editor_class": VideoLoopEditor,
        "options": [
            {
                "id": "n",
                "label": "Number of Repeats",
                "type": "number",
                "min": 1,
                "max": 10,
                "default": 1,
            }
        ]
    },
    "video_crop": {
        "name": "Crop & Aspect Ratio",
        "editor_class": VideoCropEditor,
        "options": [
            {
                "id": "aspect_ratio_presets",
                "label": "Aspect Ratio Presets",
                "type": "aspect-ratio-group",
                "buttons": [
                    {"value": "free", "label": "Free"},
                    {"value": "1:1", "label": "1:1"},
                    {"value": "4:3", "label": "4:3"},
                    {"value": "3:2", "label": "3:2"},
                    {"value": "16:9", "label": "16:9"},
                    {"value": "9:16", "label": "9:16"},
                    {"value": "2:3", "label": "2:3"},
                ]
            },
            {"id": "x1", "type": "hidden", "default": 0},
            {"id": "y1", "type": "hidden", "default": 0},
            {"id": "x2", "type": "hidden", "default": 100},
            {"id": "y2", "type": "hidden", "default": 100},
        ]
    },
    "video_rotate": {
        "name": "Rotate",
        "editor_class": VideoRotateEditor,
        "options": [
            # NEW: Preset buttons for quick rotation
            {
                "id": "angle",
                "label": "Quick Rotation Presets",
                "type": "button-group",  # Custom type for button group
                "buttons": [
                    {"value": 90, "label": "90°"},
                    {"value": 180, "label": "180°"},
                    {"value": 270, "label": "270°"},
                ]
            },
            # Existing Angle slider
            {
                "id": "angle",
                "label": "Angle (°)",
                "type": "slider",
                "min": 0,
                "max": 360,
                "step": 1,
                "default": 0,
            }
        ]
    },
    "video_resize": {
        # ... (Resize tool config remains unchanged)
        "name": "Resize",
        "editor_class": VideoResizeEditor,
        "options": [
            {
                "id": "width",
                "label": "New Width",
                "type": "number",
                "min": 1,
                "default": 0,
            },
            {
                "id": "height",
                "label": "New Height",
                "type": "number",
                "min": 1,
                "default": 0,
            },
        ]
    },
    "video_filter": {
        "name": "Video Filters",
        "editor_class": VideoColorEditor,
        "options": [
            {
                "id": "brightness",
                "label": "Brightness",
                "type": "slider",
                "min": -1.0,
                "max": 1.0,
                "step": 0.1,
                "default": 0.0,
            },
            {
                "id": "contrast",
                "label": "Contrast",
                "type": "slider",
                "min": -1.0,
                "max": 1.0,
                "step": 0.1,
                "default": 0.0,
            },
            {
                "id": "intensity",
                "label": "Color Intensity",
                "type": "slider",
                "min": 0.0,
                "max": 5.0,
                "step": 0.1,
                "default": 1.0,
            },
        ]
    },
    "video_grayscale": {
        "name": "Grayscale Effect",
        "editor_class": VideoGrayscaleEditor,
        "options": [
            {
                "id": "enabled",
                "label": "Enable Grayscale",
                "type": "checkbox",
                "default": "true"
            }
        ]
    },
    "video_tint": {
        "name": "Color Tint (RGB)",
        "editor_class": VideoTintEditor,
        "options": [
            {
                "id": "tint_color",
                "label": "Pick Tint Color",
                "type": "color",
                "default": "#ff0000"
            }
        ]
    },
    "video_painting": {
        "name": "Artistic Painting",
        "editor_class": VideoPaintingEditor,
        "options": [
            {"id": "saturation", "label": "Saturation", "type": "slider", "min": 1.0, "max": 3.0, "step": 0.1, "default": 1.5},
        ]
    },
    "video_fade": {
        "name": "Fade Transitions",
        "editor_class": VideoFadeEditor,
        "options": [
            {
                "id": "fade_in",
                "label": "Fade In Duration (sec)",
                "type": "number",
                "min": 0,
                "max": 10,
                "default": 1,
            },
            {
                "id": "fade_out",
                "label": "Fade Out Duration (sec)",
                "type": "number",
                "min": 0,
                "max": 10,
                "default": 1,
            }
        ]
    },
    "video_watermark": {
        "name": "Video Text Watermark",
        "editor_class": VideoWatermarkEditor,
        "options": [
            {
                "id": "text",
                "label": "Watermark Text",
                "type": "text",
                "default": "Copyright 2026",
            },
            {
                "id": "font_size",
                "label": "Font Size",
                "type": "number",
                "min": 10,
                "max": 200,
                "default": 40,
            },
            {
                "id": "color",
                "label": "Text Color",
                "type": "color",
                "default": "#FFFFFF",
            }
        ]
    },
    "video_image_overlay": {
        "name": "Video Logo Overlay",
        "editor_class": VideoImageWatermarkEditor,
        "options": [
            {
                "id": "image_path",
                "label": "Select Logo (Path)",
                "type": "text",
                "default": "",
            },
            {
                "id": "opacity",
                "label": "Opacity",
                "type": "slider",
                "min": 0.0,
                "max": 1.0,
                "step": 0.1,
                "default": 1.0,
            },
            {
                "id": "scale",
                "label": "Scale Factor",
                "type": "slider",
                "min": 0.1,
                "max": 2.0,
                "step": 0.1,
                "default": 1.0,
            },
            {
                "id": "position_presets",
                "label": "Position",
                "type": "select",
                "choices": [
                    {"value": "center", "label": "Center"},
                    {"value": "top-left", "label": "Top Left"},
                    {"value": "top-right", "label": "Top Right"},
                    {"value": "bottom-left", "label": "Bottom Left"},
                    {"value": "bottom-right", "label": "Bottom Right"},
                ],
                "default": "bottom-right"
            }
        ]
    }

}
