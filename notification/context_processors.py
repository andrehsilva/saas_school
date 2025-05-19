# notification/context_processors.py

from .models import NotificationRecipient
from django.db.models import Q

def header_notifications(request):
    if not request.user.is_authenticated:
        return {}

    # Notificações não lidas
    unread = NotificationRecipient.objects.filter(
        user=request.user,
        is_read=False
    ).select_related('notification').order_by('-notification__created_at')[:10]

    return {
        'header_notifications': unread
    }

def notification_count(request):
    if request.user.is_authenticated:
        count = NotificationRecipient.objects.filter(user=request.user, is_read=False).count()
    else:
        count = 0
    return {'notification_unread_count': count}