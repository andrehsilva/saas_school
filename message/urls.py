from django.urls import path
from .views import messages_timeline
urlpatterns = [
    path("", messages_timeline, name="messages_timeline"),

]
