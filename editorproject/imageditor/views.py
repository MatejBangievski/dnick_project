# views.py (FULL UPDATED CODE)

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

try:
    from .config import EDITOR_TOOLS
except ImportError:
    EDITOR_TOOLS = {}
    print(
        "\n!!! CRITICAL ERROR: Could not import EDITOR_TOOLS. Check the import path in views.py and check config.py for syntax errors. !!!\n")

# --- Configuration ---
TEMP_IMAGE_DIR = 'temp_edited_images'


# --- Cleanup Logic (Task 1) ---

def cleanup_temp_images():
    """
    Deletes the entire temporary image directory and immediately recreates it.
    This runs on server shutdown/reload.
    """
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
    """
    Initializes the temporary directory for saving images.
    Called on initial module load.
    """
    if not hasattr(settings, 'MEDIA_ROOT') or not settings.MEDIA_ROOT:
        print("ERROR: settings.MEDIA_ROOT is not configured. File handling will fail.")
        return

    temp_path = os.path.join(settings.MEDIA_ROOT, TEMP_IMAGE_DIR)
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)


setup_temp_dir()


def generate_temp_file_path(extension='png'):
    """Generates a unique path within the temporary media directory."""
    filename = f"{uuid.uuid4()}.{extension}"
    return os.path.join(TEMP_IMAGE_DIR, filename)


def parse_options(options_json):
    """Converts JSON string options into a Python dictionary with correct types."""
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


# --- Django Views ---

def editor_page(request):
    """
    Renders the main image editor page.
    """
    print(f"\n[DEBUG] EDITOR_TOOLS size after import: {len(EDITOR_TOOLS)} keys.")

    serializable_tools = {}
    # Create the dictionary that excludes 'editor_class'
    for key, tool_config in EDITOR_TOOLS.items():
        serializable_tool_config = {
            k: v for k, v in tool_config.items() if k != "editor_class"
        }
        serializable_tools[key] = serializable_tool_config

    print(f"[DEBUG] Serializable tools size: {len(serializable_tools)} keys.")

    context = {
        'template_tools': serializable_tools,
        'js_editor_tools': json.dumps(serializable_tools),
    }

    print(f"[DEBUG] js_editor_tools JSON string length: {len(context['js_editor_tools'])}")

    return render(request, 'imageditor/editor_page.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def initial_upload(request):
    """
    Saves the original file and creates a WORKING COPY for editing.
    Returns the path to the working copy. (Task 2: Copy)
    """
    if 'image' not in request.FILES:
        return JsonResponse({"success": False, "error": "No image uploaded."}, status=400)

    uploaded_file = request.FILES['image']
    name, ext = os.path.splitext(uploaded_file.name)
    file_ext = (ext[1:] or 'png').lower()

    # 1. Save the ORIGINAL file (immutable state)
    original_file_path = generate_temp_file_path(file_ext)
    default_storage.save(original_file_path, uploaded_file)

    # 2. Create the WORKING COPY from the original file
    working_file_path = generate_temp_file_path(file_ext)
    default_storage.save(working_file_path, default_storage.open(original_file_path))

    temp_image_url = settings.MEDIA_URL + working_file_path

    return JsonResponse({
        "success": True,
        "original_file_path": original_file_path,
        "working_file_path": working_file_path,
        "temp_image_url": temp_image_url
    })


@csrf_exempt
@require_http_methods(["POST"])
def reset_image_state(request):
    """
    Deletes the current working copy and creates a new one from the original image. (Task 3: Reset)
    """
    original_file_path = request.POST.get('original_file_path')
    working_file_path = request.POST.get('working_file_path')

    if not original_file_path:
        return JsonResponse({'error': 'Original file path missing.'}, status=400)

    try:
        # Delete old working copy if it exists
        if working_file_path and default_storage.exists(working_file_path):
            default_storage.delete(working_file_path)

            # Get the file extension from the original path
        name, ext = os.path.splitext(original_file_path)
        file_ext = ext[1:].lower() or 'png'

        # Create a brand new working file path
        new_working_file_path = generate_temp_file_path(file_ext)

        # Copy the original file to the new working path
        with default_storage.open(original_file_path, 'rb') as original_file:
            default_storage.save(new_working_file_path, ContentFile(original_file.read()))

        temp_image_url = settings.MEDIA_URL + new_working_file_path

        return JsonResponse({
            "success": True,
            "working_file_path": new_working_file_path,
            "temp_image_url": temp_image_url
        })

    except FileNotFoundError:
        # This error is now much less likely if cleanup_temp_images recreates the folder
        return JsonResponse({"success": False, "error": "Original image file not found on server."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Reset error: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def process_image(request):
    """
    Processes the image from the working copy path, applies the effect,
    and SAVES THE RESULT BACK TO THE SAME WORKING COPY file. (Task 2: Apply)
    This is the COMMIT action.
    """
    try:
        working_file_path = request.POST.get('current_file_path')
        tool_key = request.POST.get('tool_key')
        options_json = request.POST.get('options')

        if not working_file_path or not tool_key or not options_json:
            return JsonResponse({'error': 'Missing state path, tool key, or options.'}, status=400)

        # 1. Load the working copy
        full_path = default_storage.path(working_file_path)
        image = Image.open(full_path)

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

        name, ext = os.path.splitext(working_file_path)
        file_ext = ext[1:].lower()

        if file_ext in ['jpg', 'jpeg'] and edited_image.mode == 'RGB':
            edited_image.save(output, format='JPEG', quality=90)
        else:
            edited_image.save(output, format='PNG')
            file_ext = 'png'

        output.seek(0)

        # 2. Delete the old working file and save the new edited version over it
        default_storage.delete(working_file_path)
        saved_path = default_storage.save(working_file_path, ContentFile(output.read()))

        temp_image_url = settings.MEDIA_URL + saved_path

        return JsonResponse({
            "success": True,
            "temp_image_url": temp_image_url,
            "file_path": saved_path
        })

    except FileNotFoundError:
        return JsonResponse({"success": False, "error": "Image file not found on server."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Processing error: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def download_image(request):
    """Downloads the current working file path."""
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