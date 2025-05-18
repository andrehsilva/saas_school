from django.urls import path
from . import views  # Importação correta do módulo de views

app_name = "message"

urlpatterns = [
    path("", views.messages_timeline, name="messages_timeline"),
    
    # URL unificada para detalhes (substitui as duas anteriores)
    path("detail/<str:item_type>/<int:id>/", views.message_detail, name="message_detail"),
    
    path("calendar/", views.calendar_view, name="calendar"),
    path("event/json/", views.event_json, name="eventos_json"),
    path('mark-read/<str:item_type>/<int:item_id>/', views.mark_as_read, name='mark_as_read'),
]