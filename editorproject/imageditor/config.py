# imageditor/config.py
from .editors.editors import CropEditor, FilterEditor, ResizeEditor, RotateEditor, SubtitleEditor, WatermarkEditor

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
                "id": "align",
                "label": "Alignment",
                "type": "select",
                "default": "center",
                "choices": [
                    {"value": "left", "label": "Left"},
                    {"value": "center", "label": "Center"},
                    {"value": "right", "label": "Right"},
                ]
            },
            {
                "id": "rect",
                "label": "Background Box",
                "type": "checkbox",
                "default": False,
            },
        ]
    },
}
