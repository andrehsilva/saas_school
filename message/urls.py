from django.urls import path
from . import views  # Importação correta do módulo de views

app_name = "message"

# message/urls.py (modificado)
urlpatterns = [
    path("", views.messages_timeline, name="messages_timeline"),
    path("detail/message/<int:id>/", views.message_detail, name="message_detail"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("event/json/", views.event_json, name="eventos_json"),
]