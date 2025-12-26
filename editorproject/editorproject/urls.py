from django.contrib import admin
from django.urls import path

# Use top-level app import (this matches INSTALLED_APPS and prevents ModuleNotFoundError)
from imageditor import views as editor_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', editor_views.editor_page, name='editor_page'),

    path('api/upload/initial/', editor_views.initial_upload, name='initial_upload'),
    path('api/upload/overlay/', editor_views.upload_overlay_image, name='upload_overlay_image'),
    path('api/preview/', editor_views.preview_image, name='preview_image'), # NEW: For live non-committing updates
    path('api/process/', editor_views.process_image, name='process_image'), # COMMIT: For final "Apply Changes"
    path('api/reset_state/', editor_views.reset_image_state, name='reset_image_state'),
    path('api/reset_preview/', editor_views.reset_preview_to_working, name='reset_preview'),
    path('api/download/', editor_views.download_image, name='download_image'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)