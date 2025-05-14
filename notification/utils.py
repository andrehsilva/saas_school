from .models import Notification
from django.contrib.auth import get_user_model
User = get_user_model()

def send_notification(recipient=None, recipient_id=None, title="", message="", url=None):
    if recipient is None and recipient_id is not None:
        recipient = User.objects.get(id=recipient_id)
    Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        url=url
    )
