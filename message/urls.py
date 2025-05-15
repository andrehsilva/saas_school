from django.urls import path
from .views import (
    messages_timeline,
    message_detail,
    calendario_view,
    eventos_json,
)

app_name = "message"

urlpatterns = [
    path("", messages_timeline, name="messages_timeline"),
    path("<int:id>/", message_detail, name="message_detail"),
    path("calendario/", calendario_view, name="calendario"),
    path("eventos/json/", eventos_json, name="eventos_json"),
]