# notification/views.py
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification
from .utils import get_user_notifications
from message.utils import get_user_visibility_context

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
    context = get_user_visibility_context(request.user)
    user_ids = [request.user.id] + context["student_user_ids"]

    try:
        notification = Notification.objects.get(id=notification_id, recipient__id__in=user_ids)
    except Notification.DoesNotExist:
        raise Http404("Notificação não encontrada ou não pertence a você.")

    notification.read = True
    notification.save()

    return redirect(notification.url or '/')