# notification/views.py

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from .models import NotificationRecipient

@login_required
def unread_notifications(request):
    notifications = NotificationRecipient.objects.filter(
        user=request.user, is_read=False
    ).select_related('notification').order_by('-notification__created_at')[:10]

    data = [{
        'id': nr.notification.id,
        'title': nr.notification.title,
        'message': nr.notification.message,
        'url': nr.notification.url,
        'created_at': nr.notification.created_at.strftime("%d/%m/%Y %H:%M"),
    } for nr in notifications]
    
    return JsonResponse({'notifications': data})


@login_required
def read_and_redirect(request, notification_id):
    nr = get_object_or_404(
        NotificationRecipient, notification_id=notification_id, user=request.user
    )
    nr.is_read = True
    nr.save()
    return redirect(nr.notification.url or '/')


