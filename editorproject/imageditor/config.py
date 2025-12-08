from .editors.editors import CropEditor, FilterEditor, ResizeEditor, RotateEditor, SubtitleEditor, WatermarkEditor

# Define all tools and their configuration for the UI and backend logic
# This structure makes the app scalable for future tools.

# UI element types: 'slider', 'number', 'text', 'select', 'checkbox', 'button', 'color'
EDITOR_TOOLS = {
    "filter": {
        "name": "Filters & Enhancement",
        "editor_class": FilterEditor,
        "options": [
            {
                "id": "filter",
                "label": "Select Filter",
                "type": "select",
                "default": "none", # UPDATED: Default is now 'none'
                "choices": [
                    {"value": "none", "label": "None"}, # ADDED: The neutral option
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
                "default": 1.0, # Neutral factor is usually 1.0
                "applies_to": ["brighten", "contrast", "sepia"]
            },
            {
                "id": "radius",
                "label": "Blur Radius",
                "type": "slider",
                "min": 0,
                "max": 10,
                "step": 1,
                "default": 0, # Neutral radius is 0
                "applies_to": ["blur"]
            },
        ]
    },
    "rotate": {
        "name": "Rotate",
        "editor_class": RotateEditor,
        "options": [
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
        "name": "Resize",
        "editor_class": ResizeEditor,
        "options": [
            {
                "id": "width",
                "label": "New Width",
                "type": "number",
                "min": 1,
                "default": 0, # UPDATED: Placeholder '0', will be set by JS
            },
            {
                "id": "height",
                "label": "New Height",
                "type": "number",
                "min": 1,
                "default": 0, # UPDATED: Placeholder '0', will be set by JS
            },
        ]
    },
    "subtitle": {
        "name": "Add Text/Subtitle",
        "editor_class": SubtitleEditor,
        "options": [
            {
                "id": "text",
                "label": "Text",
                "type": "text",
                "default": "", # UPDATED: Set to empty string
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
                "default": 0, # UPDATED: Neutral default is 0
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