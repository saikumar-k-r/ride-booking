from django.db import models
from django.conf import settings


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="app_notifications"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=50)
    is_read = models.BooleanField(default=False)
    event_id = models.CharField(
    max_length=255,   
    null=True,
    blank=True,
    unique=True
   )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
     ordering = ["-created_at"]

     constraints = [
        models.UniqueConstraint(
            fields=["event_id"],
            name="unique_notification_event"
        ),
    ]

    def __str__(self):
        return f"{self.user} - {self.title}"
# Create your models here.
