from django.urls import path
from .views import (
    messages_timeline,
    message_detail,
    calendar_view,
    event_json,
)

app_name = "message"

urlpatterns = [
    path("", messages_timeline, name="messages_timeline"),
    path("<int:id>/", message_detail, name="message_detail"),
    path("calendar/", calendar_view, name="calendar"),
    path("event/json/", event_json, name="eventos_json"),
]