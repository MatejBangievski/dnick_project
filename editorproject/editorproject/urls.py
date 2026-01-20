from django.contrib import admin
from django.urls import path

from imageditor import views as editor_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', editor_views.home, name='home'),
    path('image-editor/', editor_views.editor_page, name='editor_page'),
    path('video-editor/', editor_views.video_editor_page, name='video_editor_page'),
    path('ai-editor/', editor_views.ai_editor_page, name='ai_editor_page'),

    path('api/upload/initial/', editor_views.initial_upload, name='initial_upload'),
    path('api/upload/overlay/', editor_views.upload_overlay_image, name='upload_overlay_image'),
    path('api/preview/', editor_views.preview_image, name='preview_image'), # NEW: For live non-committing updates
    path('api/process/', editor_views.process_image, name='process_image'), # COMMIT: For final "Apply Changes"
    path('api/reset_state/', editor_views.reset_image_state, name='reset_image_state'),
    path('api/reset_preview/', editor_views.reset_preview_to_working, name='reset_preview'),
    path('api/download/', editor_views.download_image, name='download_image'),
    path('api/preview-video/', editor_views.preview_video, name='preview_video'),
    path('api/task-status/<str:task_id>/', editor_views.check_task_status, name='check_task_status'),
    path('api/initial-video-upload/', editor_views.initial_video_upload, name='initial_video_upload'),
    path('api/download-video/', editor_views.download_video, name='download_video'),
    path('api/process-video/', editor_views.process_video, name='process_video'), # Fixes the NoReverseMatch
    path('api/reset-video/', editor_views.reset_video_state, name='reset_video_state'), # Fixes the NoReverseMatch
    path('api/generate-ai-image/', editor_views.generate_ai_image, name='generate_ai_image'),
    path('api/save-to-profile/', editor_views.save_to_profile, name='save_to_profile'),

    path("register/", editor_views.register, name="register"),
    path("login/", editor_views.login_request, name="login"),
    path("logout/", editor_views.logout_request, name="logout"),
    path("profile/", editor_views.profile, name="profile"),
    path("profile/edit/", editor_views.profile_edit, name="profile_edit"),
    path("profile/password/", editor_views.password_change, name="password_change"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
