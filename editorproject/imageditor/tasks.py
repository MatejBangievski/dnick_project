from celery import shared_task
from moviepy import VideoFileClip
from django.core.files.storage import default_storage
from .config import EDITOR_TOOLS
from .editors import videoEditors


@shared_task(bind=True)
def process_video_task(self, tool_key, options, working_path, preview_path):
    """
    Background task to process video optimized for speed.
    """
    input_full_path = default_storage.path(working_path)
    output_full_path = default_storage.path(preview_path)

    tool_config = EDITOR_TOOLS.get(tool_key)
    if tool_config is None:
        raise ValueError(f"Tool '{tool_key}' not found in EDITOR_TOOLS. Available: {list(EDITOR_TOOLS.keys())}")

    editor_instance = tool_config["editor_class"]()

    with VideoFileClip(input_full_path) as video:
        edited = editor_instance.edit(video, **options)


        edited.write_videofile(
            output_full_path,
            codec="libx264",
            audio_codec="aac",
            pixel_format="yuv420p",
            preset="ultrafast",
            threads=4,
        )

    return {"status": "Complete", "preview_path": preview_path}