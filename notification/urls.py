# notification/urls.py

from django.urls import path
from message.views import mark_as_read
from . import views

app_name = "notification"

urlpatterns = [
    path('unread/', views.unread_notifications, name='unread'),  # Ex: /notification/unread/
    path('read/<int:notification_id>/', views.read_and_redirect, name='read'),  # Ex: /notification/read/5/
    path('mark-read/<str:item_type>/<int:item_id>/', mark_as_read, name='mark_as_read'),

]
