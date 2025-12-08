from django.contrib import admin
from django.urls import path

# Prefer top-level app import; fallback to package-qualified import
try:
    from imageditor import views as editor_views
except ModuleNotFoundError:
    from editorproject.imageditor import views as editor_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', editor_views.editor_page, name='editor_page'),

    path('api/upload/initial/', editor_views.initial_upload, name='initial_upload'),
    path('api/process/', editor_views.process_image, name='process_image'), # This is now the COMMIT/APPLY step
    path('api/reset_state/', editor_views.reset_image_state, name='reset_image_state'), # NEW RESET URL
    path('api/download/', editor_views.download_image, name='download_image'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)