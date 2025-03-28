from django.urls import path
from .views import messages_timeline  # Certifique-se que essa view existe!

urlpatterns = [
    path('', messages_timeline, name='messages_timeline'),  # URL raiz do app
]