import io
import os
import json
import uuid
import shutil
import atexit
from django.conf import settings
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
from copy import deepcopy

# Attempt to import tools config; fall back to an empty dict so the module remains importable
try:
    from .config import EDITOR_TOOLS as BASE_EDITOR_TOOLS
except Exception:
    BASE_EDITOR_TOOLS = {}
    print(
        "\n!!! WARNING: Could not import EDITOR_TOOLS from imageditor.config; using empty toolset. Check config.py for syntax errors. !!!\n")

# Make a working copy of the base editor tools for runtime modifications
EDITOR_TOOLS = deepcopy(BASE_EDITOR_TOOLS)

# --- Configuration ---
TEMP_IMAGE_DIR = 'temp_edited_images'


# ... (Cleanup Logic, atexit.register, setup_temp_dir, generate_temp_file_path, parse_options remain unchanged)
# ... (All utility functions remain the same as the previous response)

def cleanup_temp_images():
    # ... (unchanged)
    if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
        temp_path = os.path.join(settings.MEDIA_ROOT, TEMP_IMAGE_DIR)

        # 1. DELETE: Delete the entire directory if it exists
        if os.path.exists(temp_path):
            try:
                print(f"\n[Cleanup] 🗑️ Deleting temporary images directory: {temp_path}")
                shutil.rmtree(temp_path)
                print("[Cleanup] ✅ Temporary images deleted.")
            except Exception as e:
                print(f"[Cleanup] ❌ Error during deletion: {e}")

        # 2. RECREATE: Ensure the directory exists after cleanup (critical for reloads)
        try:
            os.makedirs(temp_path, exist_ok=True)
            print("[Cleanup] 📁 Recreated temporary directory for future use.")
        except Exception as e:
            print(f"[Cleanup] ❌ Error recreating directory: {e}")


# Register the cleanup function to run when the Python interpreter exits
atexit.register(cleanup_temp_images)


def setup_temp_dir():
    # ... (unchanged)
    if not hasattr(settings, 'MEDIA_ROOT') or not settings.MEDIA_ROOT:
        print("ERROR: settings.MEDIA_ROOT is not configured. File handling will fail.")
        return

    temp_path = os.path.join(settings.MEDIA_ROOT, TEMP_IMAGE_DIR)
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)


setup_temp_dir()


def generate_temp_file_path(extension='png'):
    # ... (unchanged)
    filename = f"{uuid.uuid4()}.{extension}"
    return os.path.join(TEMP_IMAGE_DIR, filename)


def generate_stable_file_paths(extension='png'):
    """
    Generate stable file paths for a single upload session using one UUID.
    This prevents file duplication by ensuring the same 3 files are reused throughout the session.

    Returns:
        tuple: (original_path, working_path, preview_path)
    """
    session_id = uuid.uuid4().hex[:12]  # Shorter UUID for cleaner filenames
    original_path = os.path.join(TEMP_IMAGE_DIR, f"original_{session_id}.{extension}")
    working_path = os.path.join(TEMP_IMAGE_DIR, f"working_{session_id}.{extension}")
    preview_path = os.path.join(TEMP_IMAGE_DIR, f"preview_{session_id}.{extension}")
    return original_path, working_path, preview_path


def cleanup_session_files(original_path, working_path, preview_path):
    """
    Clean up all three files from a previous session when uploading a new image.
    This ensures we don't accumulate files from multiple uploads.
    """
    for file_path in [original_path, working_path, preview_path]:
        try:
            if file_path and default_storage.exists(file_path):
                default_storage.delete(file_path)
                print(f"[Session Cleanup] Deleted old file: {file_path}")
        except Exception as e:
            print(f"[Session Cleanup] Error deleting {file_path}: {e}")


def parse_options(options_json):
    """Parse and convert options from JSON string, handling type conversions."""
    options = json.loads(options_json)

    # Fields that should NEVER be converted to numbers (keep as strings)
    KEEP_AS_STRING = {
        'text',  # Text content for subtitles
        'font_name',  # Font family name
        'filter',  # Filter name
        'align',  # Text alignment
        'position',  # Position name
        'style',  # Font style
        'watermark',  # File path
        'select_filter',  # Selected filter name
    }

    # Color fields that need hex to RGB conversion
    COLOR_FIELDS = {
        'font_color',  # Hex color code (e.g., "#FFFFFF")
        'stroke_color',  # Hex color code
        'rect_color',  # Hex color code
        'shadow_color',  # Hex color code
    }

    def hex_to_rgb(hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        return (255, 255, 255)  # Default to white if invalid

    for key, value in options.items():
        # Convert hex colors to RGB tuples
        if key in COLOR_FIELDS and isinstance(value, str) and value.startswith('#'):
            options[key] = hex_to_rgb(value)
            continue

        if isinstance(value, str):
            # Skip numeric conversion for text-based fields
            if key in KEEP_AS_STRING:
                continue

            # Convert booleans
            if value.lower() in ('true', 'false'):
                options[key] = value.lower() == 'true'
            else:
                # Try to convert to number only if it's NOT a text field
                try:
                    options[key] = int(value)
                except ValueError:
                    try:
                        options[key] = float(value)
                    except ValueError:
                        pass  # Keep as string if conversion fails
    return options


def get_image_dimensions(file_path):
    """Utility to get width and height from a stored image file."""
    try:
        full_path = default_storage.path(file_path)
        with Image.open(full_path) as img:
            return img.size
    except Exception:
        return 0, 0


# --- Django Views ---

def editor_page(request):
    """
    Renders the main image editor page.
    The tools list is rendered here, and the initial tool configuration
    doesn't require image dimensions yet.
    """

    # We use a copy of the base tools to ensure the frontend always gets the base defaults
    current_tools = deepcopy(BASE_EDITOR_TOOLS)

    serializable_tools = {}
    for key, tool_config in current_tools.items():
        serializable_tool_config = {
            k: v for k, v in tool_config.items() if k != "editor_class"
        }
        serializable_tools[key] = serializable_tool_config

    context = {
        'template_tools': serializable_tools,
        'js_editor_tools': json.dumps(serializable_tools),
    }

    return render(request, 'imageditor/editor_page.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def initial_upload(request):
    """
    Saves the original file, creates copies, and returns the image dimensions
    and the tool configuration with current dimensions for the Resize tool.

    OPTIMIZATION: Uses stable file paths to prevent file duplication.
    """
    if 'image' not in request.FILES:
        return JsonResponse({"success": False, "error": "No image uploaded."}, status=400)

    uploaded_file = request.FILES['image']
    name, ext = os.path.splitext(uploaded_file.name)
    file_ext = (ext[1:] or 'png').lower()

    # OPTIMIZATION: Check if user had previous session files and clean them up
    old_original = request.POST.get('old_original_path')
    old_working = request.POST.get('old_working_path')
    old_preview = request.POST.get('old_preview_path')

    if old_original or old_working or old_preview:
        cleanup_session_files(old_original, old_working, old_preview)
        print(f"[Session Cleanup] Cleaned up previous session files before new upload")

    # OPTIMIZATION: Generate stable file paths using descriptive names and single session UUID
    original_file_path, working_file_path, preview_file_path = generate_stable_file_paths(file_ext)

    # 1. Save the ORIGINAL file (immutable state)
    default_storage.save(original_file_path, uploaded_file)

    # 2. Create the WORKING COPY from the original file (Committed State)
    default_storage.save(working_file_path, default_storage.open(original_file_path))

    # 3. Create an initial PREVIEW file (Transient State)
    default_storage.save(preview_file_path, default_storage.open(working_file_path))

    # Get dimensions of the uploaded image
    width, height = get_image_dimensions(working_file_path)

    temp_image_url = settings.MEDIA_URL + preview_file_path

    return JsonResponse({
        "success": True,
        "original_file_path": original_file_path,
        "working_file_path": working_file_path,
        "preview_file_path": preview_file_path,
        "image_width": width,
        "image_height": height,
        "temp_image_url": temp_image_url
    })


@csrf_exempt
@require_http_methods(["POST"])
def reset_image_state(request):
    """
    Resets working and preview copies from the original image by overwriting existing files.
    Returns the image dimensions for the Resize tool's default.

    OPTIMIZATION: Reuses existing file paths instead of creating new ones to prevent file duplication.
    """
    original_file_path = request.POST.get('original_file_path')
    working_file_path = request.POST.get('working_file_path')
    preview_file_path = request.POST.get('preview_file_path')

    if not original_file_path:
        return JsonResponse({'error': 'Original file path missing.'}, status=400)

    try:
        # OPTIMIZATION: Delete existing files to prepare for overwrite
        if working_file_path and default_storage.exists(working_file_path):
            default_storage.delete(working_file_path)
        if preview_file_path and default_storage.exists(preview_file_path):
            default_storage.delete(preview_file_path)

        # OPTIMIZATION: REUSE existing paths instead of calling generate_temp_file_path()
        # This prevents creating new files with different UUIDs

        # 1. Overwrite the WORKING file with content from ORIGINAL (Resets committed state)
        with default_storage.open(original_file_path, 'rb') as original_file:
            default_storage.save(working_file_path, ContentFile(original_file.read()))

        # 2. Overwrite the PREVIEW file with content from WORKING (Resets transient state)
        with default_storage.open(working_file_path, 'rb') as working_file:
            default_storage.save(preview_file_path, ContentFile(working_file.read()))

        # Get dimensions of the reset image
        width, height = get_image_dimensions(working_file_path)

        temp_image_url = settings.MEDIA_URL + preview_file_path

        return JsonResponse({
            "success": True,
            "working_file_path": working_file_path,  # Same path, not new_working_file_path
            "preview_file_path": preview_file_path,  # Same path, not new_preview_file_path
            "image_width": width,
            "image_height": height,
            "temp_image_url": temp_image_url
        })

    except FileNotFoundError:
        return JsonResponse({"success": False, "error": "Original image file not found on server."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Reset error: {str(e)}"}, status=500)


# NEW: Reset transient PREVIEW by copying from the committed WORKING file
@csrf_exempt
@require_http_methods(["POST"])
def reset_preview_to_working(request):
    """
    Copies the committed working file into the preview file, overwriting it.
    This is used when the user switches tools and we want to discard unsaved preview-only changes.

    OPTIMIZATION: Reuses existing preview path instead of creating a new one to prevent file duplication.

    POST parameters:
    - working_file_path (required): the path to the committed working copy in MEDIA
    - current_preview_path (required): the current transient preview path to overwrite
    """
    working_file_path = request.POST.get('working_file_path')
    current_preview_path = request.POST.get('current_preview_path')

    if not working_file_path:
        return JsonResponse({'success': False, 'error': 'Missing working_file_path.'}, status=400)

    if not current_preview_path:
        return JsonResponse({'success': False, 'error': 'Missing current_preview_path.'}, status=400)

    try:
        if not default_storage.exists(working_file_path):
            return JsonResponse({'success': False, 'error': 'Working file not found.'}, status=404)

        # Delete the current preview file to prepare for overwrite
        try:
            if default_storage.exists(current_preview_path):
                default_storage.delete(current_preview_path)
        except Exception:
            # Non-fatal: ignore deletion errors
            pass

        # OPTIMIZATION: REUSE the existing current_preview_path instead of calling generate_temp_file_path()
        # This prevents creating a new file with a different UUID
        with default_storage.open(working_file_path, 'rb') as wf:
            content = ContentFile(wf.read())
            saved_path = default_storage.save(current_preview_path, content)

        temp_image_url = settings.MEDIA_URL + saved_path

        return JsonResponse({
            'success': True,
            'preview_file_path': saved_path,  # Same path as current_preview_path
            'temp_image_url': temp_image_url
        })

    except FileNotFoundError:
        return JsonResponse({'success': False, 'error': 'Working file not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Reset preview error: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def preview_image(request):
    # ... (This function remains UNCHANGED, as its logic is sound for the new architecture)
    try:
        working_file_path = request.POST.get('working_file_path')
        current_preview_path = request.POST.get('current_preview_path')
        tool_key = request.POST.get('tool_key')
        options_json = request.POST.get('options')

        if not working_file_path or not current_preview_path or not tool_key or not options_json:
            return JsonResponse({'error': 'Missing state path, tool key, or options.'}, status=400)

        # 1. Load the committed working copy
        full_path_source = default_storage.path(working_file_path)
        image = Image.open(full_path_source)

        options = parse_options(options_json)
        tool_config = EDITOR_TOOLS.get(tool_key)

        if not tool_config:
            return JsonResponse({'error': f'Unknown tool: {tool_key}'}, status=400)

        EditorClass = tool_config["editor_class"]
        editor_instance = EditorClass()

        if tool_key == 'filter':
            options['filter'] = options.pop('select_filter', options.get('filter'))

        edited_image = editor_instance.edit(image, **options)

        output = io.BytesIO()

        # Determine output format based on the committed state's extension
        name, ext = os.path.splitext(working_file_path)
        file_ext = ext[1:].lower()

        # OPTIMIZATION: Use progressive encoding and optimized compression for faster transfers
        if file_ext in ['jpg', 'jpeg']:
            if edited_image.mode not in ('RGB', 'L'):
                edited_image = edited_image.convert('RGB')
            edited_image.save(output, format='JPEG', quality=85, optimize=True, progressive=True)
        elif file_ext == 'png':
            # For PNG, use optimized compression
            edited_image.save(output, format='PNG', optimize=True, compress_level=6)
        else:
            # Default to PNG for other formats
            edited_image.save(output, format='PNG', optimize=True, compress_level=6)

        output.seek(0)

        # 2. Overwrite the PREVIEW file
        default_storage.delete(current_preview_path)
        saved_path = default_storage.save(current_preview_path, ContentFile(output.read()))

        temp_image_url = settings.MEDIA_URL + saved_path

        # Get new dimensions after editing (important for crop tool)
        new_width, new_height = edited_image.size

        response_data = {
            "success": True,
            "temp_image_url": temp_image_url,
            "preview_file_path": saved_path
        }

        # For crop tool, return new dimensions so frontend can update state
        if tool_key == 'crop':
            response_data['new_width'] = new_width
            response_data['new_height'] = new_height

        return JsonResponse(response_data, headers={
            'Cache-Control': 'no-cache, must-revalidate',  # Allow browser to cache but always revalidate
        })

    except FileNotFoundError:
        return JsonResponse({"success": False, "error": "Image file not found on server."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Preview error: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def process_image(request):
    # ... (This function remains UNCHANGED, its purpose is to copy preview to working state)
    try:
        working_file_path = request.POST.get('working_file_path')
        preview_file_path = request.POST.get('preview_file_path')

        if not working_file_path or not preview_file_path:
            return JsonResponse({'error': 'Missing working or preview path.'}, status=400)

        # 1. Read the image data from the current PREVIEW file
        full_path_source = default_storage.path(preview_file_path)

        # 2. Copy the content of the PREVIEW file into the WORKING COPY file
        with default_storage.open(full_path_source, 'rb') as source_file:
            content = ContentFile(source_file.read())

        # 3. Overwrite the WORKING COPY (Commit the change)
        default_storage.delete(working_file_path)
        saved_path = default_storage.save(working_file_path, content)

        temp_image_url = settings.MEDIA_URL + saved_path

        # Get new dimensions after committing (important for crop/resize tools)
        new_width, new_height = get_image_dimensions(saved_path)

        return JsonResponse({
            "success": True,
            "temp_image_url": temp_image_url,
            "working_file_path": saved_path,
            "new_width": new_width,
            "new_height": new_height
        })

    except FileNotFoundError:
        return JsonResponse({"success": False, "error": "Image file not found on server."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Processing error: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def download_image(request):
    # ... (unchanged)
    file_path = request.GET.get('file_path')

    if not file_path:
        return JsonResponse({"success": False, "error": "Missing file path."}, status=400)

    try:
        if not default_storage.exists(file_path):
            raise Http404("File not found.")

        full_path = default_storage.path(file_path)

        file_name = os.path.basename(file_path)
        download_name = f"edited_{uuid.uuid4().hex[:8]}_{file_name}"

        content_type = 'application/octet-stream'
        if file_name.lower().endswith('.png'):
            content_type = 'image/png'
        elif file_name.lower().endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'

        response = FileResponse(open(full_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{download_name}"'
        return response

    except FileNotFoundError:
        raise Http404("File not found.")
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Download error: {str(e)}"}, status=500)