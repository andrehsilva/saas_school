# views.py
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification
from .utils import get_user_notifications

@login_required
def unread_notifications(request):
    notifications = get_user_notifications(request.user).filter(read=False)[:10]
    return JsonResponse({
        "count": notifications.count(),
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "url": n.url or "#",
                "created_at": n.created_at.strftime("%d/%m/%Y %H:%M")
            } for n in notifications
        ]
    })

@login_required
def read_and_redirect(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.read = True
    notification.save()
    return redirect(notification.url or '/')