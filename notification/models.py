# notification/models.py

from django.db import models
from django.contrib.auth import get_user_model
from school.models import Class

User = get_user_model()

class Notification(models.Model):
    recipients = models.ManyToManyField(User, through='NotificationRecipient', related_name='notifications')
    classrooms = models.ManyToManyField(Class, blank=True, related_name='class_notifications')
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notificação: {self.title}"


class NotificationRecipient(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('notification', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.notification.title}"
