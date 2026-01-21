from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils.html import mark_safe

from .models import UserEdit

# Unregister the original User admin so we can register our custom one
admin.site.unregister(User)


class UserEditInline(admin.TabularInline):
    model = UserEdit
    extra = 0
    # Make fields readonly if you just want to see them and not add/edit them from User page,
    # but regular fields is fine too.
    readonly_fields = ('created_at', 'file_preview')
    fields = ('edited_file', 'file_preview', 'media_type', 'created_at')

    def file_preview(self, obj):
        if obj.media_type == 'image' and obj.edited_file:
            # Assuming obj.edited_file.url provides the URL.
            # CloudinaryField usually behaves like FileField.
            return mark_safe(f'<img src="{obj.edited_file.url}" style="max-height: 100px;"/>')
        elif obj.media_type == 'video' and obj.edited_file:
             return mark_safe(f'<a href="{obj.edited_file.url}" target="_blank">View Video</a>')
        return "No preview"
    file_preview.short_description = 'Preview'


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = BaseUserAdmin.inlines + (UserEditInline,)
    list_display = BaseUserAdmin.list_display + ('image_count', 'video_count')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # SQL query optimization: naming the annotation allows ordering
        qs = qs.annotate(
            _image_count=Count('useredit', filter=Q(useredit__media_type='image')),
            _video_count=Count('useredit', filter=Q(useredit__media_type='video')),
        )
        return qs

    def image_count(self, obj):
        return obj._image_count

    image_count.short_description = 'Images Saved'
    image_count.admin_order_field = '_image_count'

    def video_count(self, obj):
        return obj._video_count

    video_count.short_description = 'Videos Saved'
    video_count.admin_order_field = '_video_count'


# Register the UserEdit model separately if we want to manage Edits directly
@admin.register(UserEdit)
class UserEditAdmin(admin.ModelAdmin):
    list_display = ('user', 'media_type', 'created_at', 'edited_file')
    list_filter = ('media_type', 'created_at')
    search_fields = ('user__username',)
