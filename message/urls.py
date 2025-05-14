from django.urls import path
from .views import messages_timeline, message_detail  # Certifique-se de criar a view 'message_detail'

urlpatterns = [
    path("", messages_timeline, name="messages_timeline"),
    path("<int:id>/", message_detail, name="message_detail"),  # URL para detalhes da mensagem
]
