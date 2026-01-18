import io
import os
import json
import uuid
import shutil
import atexit
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
from copy import deepcopy
from celery.result import AsyncResult
from .tasks import process_video_task
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .forms import UserRegisterForm, UserUpdateForm

# Google Gemini imports for AI image generation
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("\n!!! WARNING: google-genai library not installed. AI editor features will be disabled. !!!\n")

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
TEMP_OVERLAY_DIR = 'temp_overlays'
AI_EDITED_IMAGE_DIR = 'temp_edited_images'  # Store AI-generated images in temp directory for session cleanup


# ... (Cleanup Logic, atexit.register, setup_temp_dir, generate_temp_file_path, parse_options remain unchanged)
# ... (All utility functions remain the same as the previous response)

def home(request):
    return render(request, 'imageditor/homepage.html')

def cleanup_temp_images():
    # ... (unchanged)
    if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
        temp_path = os.path.join(settings.MEDIA_ROOT, TEMP_IMAGE_DIR)
        overlay_path = os.path.join(settings.MEDIA_ROOT, TEMP_OVERLAY_DIR)

        # 1. DELETE: Delete the entire directory if it exists
        if os.path.exists(temp_path):
            try:
                print(f"\n[Cleanup] 🗑️ Deleting temporary images directory: {temp_path}")
                shutil.rmtree(temp_path)
                print("[Cleanup] ✅ Temporary images deleted.")
            except Exception as e:
                print(f"[Cleanup] ❌ Error during deletion: {e}")

        # Delete overlay directory
        if os.path.exists(overlay_path):
            try:
                print(f"[Cleanup] 🗑️ Deleting temporary overlays directory: {overlay_path}")
                shutil.rmtree(overlay_path)
                print("[Cleanup] ✅ Temporary overlays deleted.")
            except Exception as e:
                print(f"[Cleanup] ❌ Error during overlay deletion: {e}")

        # 2. RECREATE: Ensure the directory exists after cleanup (critical for reloads)
        try:
            os.makedirs(temp_path, exist_ok=True)
            os.makedirs(overlay_path, exist_ok=True)
            print("[Cleanup] 📁 Recreated temporary directories for future use.")
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
    overlay_path = os.path.join(settings.MEDIA_ROOT, TEMP_OVERLAY_DIR)
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
    if not os.path.exists(overlay_path):
        os.makedirs(overlay_path)


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
        'overlay_path',  # Overlay file path
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

@require_http_methods(["GET"])
@login_required
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
    This is used when the user switches tools, and we want to discard unsaved preview-only changes.

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


@csrf_exempt
@require_http_methods(["POST"])
def upload_overlay_image(request):
    """
    Upload a PNG overlay image for the overlay tool.
    Validates PNG format and saves to temp_overlays directory.
    Returns file path and dimensions.
    """
    if 'overlay_file' not in request.FILES:
        return JsonResponse({"success": False, "error": "No overlay file uploaded."}, status=400)

    uploaded_file = request.FILES['overlay_file']

    # Validate PNG format
    if not uploaded_file.name.lower().endswith('.png'):
        return JsonResponse({"success": False, "error": "Only PNG files are supported for overlays."}, status=400)

    try:
        # Generate unique filename
        filename = f"overlay_{uuid.uuid4().hex[:12]}.png"
        overlay_path = os.path.join(TEMP_OVERLAY_DIR, filename)

        # Save the file
        saved_path = default_storage.save(overlay_path, uploaded_file)

        # Get dimensions
        full_path = default_storage.path(saved_path)
        with Image.open(full_path) as img:
            width, height = img.size

            # Verify it's actually a valid PNG with alpha channel
            if img.mode not in ('RGBA', 'LA', 'P'):
                # Convert to RGBA if needed
                img = img.convert('RGBA')
                img.save(full_path, 'PNG')

        overlay_url = settings.MEDIA_URL + saved_path

        return JsonResponse({
            "success": True,
            "overlay_path": saved_path,
            "overlay_url": overlay_url,
            "width": width,
            "height": height
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": f"Failed to upload overlay: {str(e)}"}, status=500)


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


# ==========================================================================================
#                               VIDEO PROCESSING METHODS
# ==========================================================================================

@require_http_methods(["GET"])
@login_required
def video_editor_page(request):
    """
    Renders the dedicated video editor page.
    Filters the toolset to show only video-compatible tools.
    """
    current_tools = deepcopy(BASE_EDITOR_TOOLS)

    serializable_tools = {}
    for key, tool_config in current_tools.items():
        if key.startswith('video_'):
            serializable_tool_config = {
                k: v for k, v in tool_config.items() if k != "editor_class"
            }
            serializable_tools[key] = serializable_tool_config

    context = {
        'template_tools': serializable_tools,
        'js_editor_tools': json.dumps(serializable_tools),
        'media_type': 'video'
    }

    return render(request, 'imageditor/video_editor_page.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def preview_video(request):
    """
    Triggers the background Celery task for video editing.
    Returns a task_id so the frontend can poll for status.
    """
    try:
        working_file_path = request.POST.get('working_file_path')
        current_preview_path = request.POST.get('current_preview_path')
        tool_key = request.POST.get('tool_key')
        options_json = request.POST.get('options')

        if not all([working_file_path, current_preview_path, tool_key, options_json]):
            return JsonResponse({'error': 'Missing required parameters.'}, status=400)

        options = parse_options(options_json)

        task = process_video_task.delay(
            tool_key,
            options,
            working_file_path,
            current_preview_path
        )

        return JsonResponse({
            "success": True,
            "task_id": task.id
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_http_methods(["GET"])
def check_task_status(request, task_id):
    """
    Endpoint for the frontend to check if the video is finished.
    """
    result = AsyncResult(task_id)

    response_data = {
        "task_id": task_id,
        "status": result.status,
    }

    if result.status == 'SUCCESS':
        file_path = result.result.get("preview_path")
        if file_path:
            url_path = file_path.replace('\\', '/')
            response_data["preview_url"] = settings.MEDIA_URL + url_path
            response_data["preview_file_path"] = file_path

    elif result.status == 'FAILURE':
        response_data["error"] = str(result.result)

    return JsonResponse(response_data)


@require_http_methods(["GET"])
def download_video(request):
    """
    Handles the final download for processed videos.
    """
    file_path = request.GET.get('file_path')

    if not file_path:
        return JsonResponse({"success": False, "error": "Missing file path."}, status=400)

    try:
        if not default_storage.exists(file_path):
            raise Http404("Video file not found.")

        full_path = default_storage.path(file_path)
        file_name = os.path.basename(file_path)

        download_name = f"edited_video_{uuid.uuid4().hex[:8]}.mp4"

        response = FileResponse(open(full_path, 'rb'), content_type='video/mp4')
        response['Content-Disposition'] = f'attachment; filename="{download_name}"'
        return response

    except Exception as e:
        return JsonResponse({"success": False, "error": f"Download error: {str(e)}"}, status=500)

from moviepy import VideoFileClip


@csrf_exempt
@require_http_methods(["POST"])
def process_video(request):
    """
    Finalizes the video changes by copying the transient preview
    video into the permanent working copy.
    """
    try:
        working_file_path = request.POST.get('working_file_path')
        preview_file_path = request.POST.get('preview_file_path')

        if not working_file_path or not preview_file_path:
            return JsonResponse({'error': 'Missing working or preview path.'}, status=400)

        full_path_source = default_storage.path(preview_file_path)

        with default_storage.open(full_path_source, 'rb') as source_file:
            content = ContentFile(source_file.read())

        if default_storage.exists(working_file_path):
            default_storage.delete(working_file_path)

        saved_path = default_storage.save(working_file_path, content)

        return JsonResponse({
            "success": True,
            "working_file_path": saved_path,
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": f"Video Commit error: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def reset_video_state(request):
    """
    Resets the video by copying the original file back onto the working and preview files.
    """
    original_path = request.POST.get('original_file_path')
    working_path = request.POST.get('working_file_path')
    preview_path = request.POST.get('preview_file_path')

    try:
        with default_storage.open(original_path, 'rb') as f:
            content = f.read()
            if default_storage.exists(working_path): default_storage.delete(working_path)
            default_storage.save(working_path, ContentFile(content))
            if default_storage.exists(preview_path): default_storage.delete(preview_path)
            default_storage.save(preview_path, ContentFile(content))

        return JsonResponse({"success": True, "temp_video_url": settings.MEDIA_URL + original_path})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def initial_video_upload(request):
    if 'video' not in request.FILES:
        return JsonResponse({"success": False, "error": "No video uploaded."}, status=400)

    uploaded_file = request.FILES['video']
    name, ext = os.path.splitext(uploaded_file.name)
    file_ext = (ext[1:] or 'mp4').lower()

    orig_name, work_name, prev_name = generate_stable_file_paths(file_ext)

    actual_original_path = default_storage.save(orig_name, uploaded_file)

    with default_storage.open(actual_original_path) as f:
        content = f.read()
        actual_working_path = default_storage.save(work_name, ContentFile(content))
        actual_preview_path = default_storage.save(prev_name, ContentFile(content))

    try:
        full_path = default_storage.path(actual_working_path)
        with VideoFileClip(full_path) as clip:
            width, height = clip.w, clip.h
    except Exception as e:
        print(f"Error getting video dimensions: {e}")
        width, height = 0, 0

    return JsonResponse({
        "success": True,
        "original_file_path": actual_original_path,  # Sync this with JS
        "working_file_path": actual_working_path,
        "preview_file_path": actual_preview_path,
        "video_width": width,
        "video_height": height,
        "temp_video_url": settings.MEDIA_URL + actual_original_path  # Start with original
    })


# ============================================
# AI EDITOR VIEWS (Gemini 2.5 Flash Integration)
# ============================================

@require_http_methods(["GET"])
@login_required
def ai_editor_page(request):
    """
    Renders the AI image generation page with chatbot interface.
    Allows transferring images from the main editor via URL parameters.
    """
    # Get image paths from URL parameters if coming from editor
    original_path = request.GET.get('original_path', '')
    working_path = request.GET.get('working_path', '')
    preview_path = request.GET.get('preview_path', '')

    context = {
        'original_path': original_path,
        'working_path': working_path,
        'preview_path': preview_path,
        'has_image': bool(preview_path),
        'gemini_available': GEMINI_AVAILABLE,
    }

    return render(request, 'imageditor/ai_editor_page.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def generate_ai_image(request):
    """
    API endpoint for AI image generation using Google Gemini 2.5 Flash.
    Accepts an image and text prompt, returns the AI-generated result.
    """
    if not GEMINI_AVAILABLE:
        return JsonResponse({
            "success": False,
            "error": "Google Gemini API is not available. Please install google-genai library."
        }, status=500)

    try:
        # Get the prompt text
        prompt = request.POST.get('prompt', '').strip()
        if not prompt:
            return JsonResponse({"success": False, "error": "Prompt text is required."}, status=400)

        # Get the image - either from file upload or existing path
        image_data = None
        image_path = request.POST.get('image_path', '')

        if 'image' in request.FILES:
            # New image uploaded
            uploaded_file = request.FILES['image']
            image_data = uploaded_file.read()
        elif image_path and default_storage.exists(image_path):
            # Use existing image from editor
            with default_storage.open(image_path, 'rb') as f:
                image_data = f.read()
        else:
            return JsonResponse({"success": False, "error": "No image provided."}, status=400)

        # Get API key from environment
        api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            return JsonResponse({
                "success": False,
                "error": "GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set."
            }, status=500)

        # Initialize Gemini client
        client = genai.Client(api_key=api_key)

        # Prepare the prompt with image
        model = "gemini-2.5-flash-image"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_data, mime_type="image/png"),
                ],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        )

        # Generate AI image
        generated_image_data = None
        response_text = ""

        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                part = chunk.candidates[0].content.parts[0]

                # Check for image data
                if part.inline_data and part.inline_data.data:
                    generated_image_data = part.inline_data.data
                    break
                # Collect text responses
                elif hasattr(chunk, 'text') and chunk.text:
                    response_text += chunk.text

        if not generated_image_data:
            error_msg = "No image generated. " + (response_text if response_text else "The AI did not return an image.")
            return JsonResponse({"success": False, "error": error_msg}, status=500)

        # Save the generated image to temporary storage
        ai_image_filename = f"ai_{uuid.uuid4()}.png"
        ai_image_path = os.path.join(AI_EDITED_IMAGE_DIR, ai_image_filename)

        # Save using Django storage
        saved_path = default_storage.save(ai_image_path, ContentFile(generated_image_data))

        # Return success with image URL
        ai_image_url = settings.MEDIA_URL + saved_path

        return JsonResponse({
            "success": True,
            "image_url": ai_image_url,
            "image_path": saved_path,
            "message": response_text if response_text else "Image generated successfully"
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[AI Generation Error] {error_details}")
        return JsonResponse({
            "success": False,
            "error": f"AI generation failed: {str(e)}"
        }, status=500)


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("home")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = UserRegisterForm()
    return render(request, "imageditor/register.html", {"form": form})


def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("home")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request, "imageditor/login.html", {"form": form})


def logout_request(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("home")


@login_required
def profile(request):
    return render(request, 'imageditor/profile.html')


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'imageditor/profile_edit.html', {'form': form})


@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'imageditor/password_change.html', {'form': form})

