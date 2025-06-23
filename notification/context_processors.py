# context_processors.py
def notifications(request):
    if request.user.is_authenticated:
        return {
            'unread_notifications_count': request.user.notifications.filter(read=False).count(),
            'has_unread_notifications': request.user.notifications.filter(read=False).exists()
        }
    return {}