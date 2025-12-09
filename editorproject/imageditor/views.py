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


def parse_options(options_json):
    # ... (unchanged)
    options = json.loads(options_json)

    for key, value in options.items():
        if isinstance(value, str):
            if value.lower() in ('true', 'false'):
                options[key] = value.lower() == 'true'
            else:
                try:
                    options[key] = int(value)
                except ValueError:
                    try:
                        options[key] = float(value)
                    except ValueError:
                        pass
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
    """
    if 'image' not in request.FILES:
        return JsonResponse({"success": False, "error": "No image uploaded."}, status=400)

    uploaded_file = request.FILES['image']
    name, ext = os.path.splitext(uploaded_file.name)
    file_ext = (ext[1:] or 'png').lower()

    # 1. Save the ORIGINAL file (immutable state)
    original_file_path = generate_temp_file_path(file_ext)
    default_storage.save(original_file_path, uploaded_file)

    # 2. Create the WORKING COPY from the original file (Committed State)
    working_file_path = generate_temp_file_path(file_ext)
    default_storage.save(working_file_path, default_storage.open(original_file_path))

    # 3. Create an initial PREVIEW file (Transient State)
    preview_file_path = generate_temp_file_path(file_ext)
    default_storage.save(preview_file_path, default_storage.open(working_file_path))

    # NEW: Get dimensions of the uploaded image
    width, height = get_image_dimensions(working_file_path)

    temp_image_url = settings.MEDIA_URL + preview_file_path

    return JsonResponse({
        "success": True,
        "original_file_path": original_file_path,
        "working_file_path": working_file_path,
        "preview_file_path": preview_file_path,
        # NEW: Send dimensions to the frontend
        "image_width": width,
        "image_height": height,
        "temp_image_url": temp_image_url
    })


@csrf_exempt
@require_http_methods(["POST"])
def reset_image_state(request):
    """
    Deletes old copies, creates new working and preview copies from the original image,
    and returns the image dimensions for the Resize tool's default.
    """
    original_file_path = request.POST.get('original_file_path')
    working_file_path = request.POST.get('working_file_path')
    preview_file_path = request.POST.get('preview_file_path')

    if not original_file_path:
        return JsonResponse({'error': 'Original file path missing.'}, status=400)

    try:
        # Delete old copies
        if working_file_path and default_storage.exists(working_file_path):
            default_storage.delete(working_file_path)
        if preview_file_path and default_storage.exists(preview_file_path):
            default_storage.delete(preview_file_path)

            # Get file extension
        name, ext = os.path.splitext(original_file_path)
        file_ext = ext[1:].lower() or 'png'

        # 1. Create brand new working file path (Resets committed state)
        new_working_file_path = generate_temp_file_path(file_ext)
        with default_storage.open(original_file_path, 'rb') as original_file:
            default_storage.save(new_working_file_path, ContentFile(original_file.read()))

        # 2. Create brand new preview file path (Resets transient state)
        new_preview_file_path = generate_temp_file_path(file_ext)
        with default_storage.open(new_working_file_path, 'rb') as working_file:
            default_storage.save(new_preview_file_path, ContentFile(working_file.read()))

        # NEW: Get dimensions of the newly reset image
        width, height = get_image_dimensions(new_working_file_path)

        temp_image_url = settings.MEDIA_URL + new_preview_file_path

        return JsonResponse({
            "success": True,
            "working_file_path": new_working_file_path,
            "preview_file_path": new_preview_file_path,
            # NEW: Send dimensions to the frontend
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
    Copies the committed working file into a new preview file and returns its path/URL.
    This is used when the user switches tools and we want to discard unsaved preview-only changes.

    POST parameters:
    - working_file_path (required): the path to the committed working copy in MEDIA
    - current_preview_path (optional): the current transient preview path to delete
    """
    working_file_path = request.POST.get('working_file_path')
    current_preview_path = request.POST.get('current_preview_path')

    if not working_file_path:
        return JsonResponse({'success': False, 'error': 'Missing working_file_path.'}, status=400)

    try:
        if not default_storage.exists(working_file_path):
            return JsonResponse({'success': False, 'error': 'Working file not found.'}, status=404)

        # Optionally delete the current preview file (we will create a fresh one)
        try:
            if current_preview_path and default_storage.exists(current_preview_path):
                default_storage.delete(current_preview_path)
        except Exception:
            # Non-fatal: ignore deletion errors
            pass

        # Determine extension from the working file
        name, ext = os.path.splitext(working_file_path)
        file_ext = ext[1:].lower() or 'png'

        # Create a brand-new preview file path and copy content from the working file
        new_preview_path = generate_temp_file_path(file_ext)
        with default_storage.open(working_file_path, 'rb') as wf:
            content = ContentFile(wf.read())
            saved_path = default_storage.save(new_preview_path, content)

        temp_image_url = settings.MEDIA_URL + saved_path

        return JsonResponse({
            'success': True,
            'preview_file_path': saved_path,
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

        if file_ext in ['jpg', 'jpeg'] and edited_image.mode == 'RGB':
            edited_image.save(output, format='JPEG', quality=90)
        else:
            edited_image.save(output, format='PNG')

        output.seek(0)

        # 2. Overwrite the PREVIEW file
        default_storage.delete(current_preview_path)
        saved_path = default_storage.save(current_preview_path, ContentFile(output.read()))

        temp_image_url = settings.MEDIA_URL + saved_path

        return JsonResponse({
            "success": True,
            "temp_image_url": temp_image_url,
            "preview_file_path": saved_path
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

        return JsonResponse({
            "success": True,
            "temp_image_url": temp_image_url,
            "working_file_path": saved_path
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