# notification/views.py

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
from django.shortcuts import get_object_or_404, redirect

@login_required
def unread_notifications(request):
    notifications = Notification.objects.filter(recipient=request.user, is_read=False)[:10]
    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'url': n.url,
        'created_at': n.created_at.strftime("%d/%m/%Y %H:%M"),
    } for n in notifications]
    return JsonResponse({'notifications': data})


@login_required
def read_and_redirect(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect(notification.url or '/')