from cloudinary.models import CloudinaryField
from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class UserEdit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # This FileField now points to Cloudinary automatically!
    edited_file = CloudinaryField(
        resource_type='auto',
        folder='edits/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    media_type = models.CharField(max_length=10, choices=[('image', 'Image'), ('video', 'Video')])

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.media_type} - {self.created_at:%Y-%m-%d}"