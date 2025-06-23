from django.urls import path
from . import views

urlpatterns = [
    
    path('unread/', views.unread_notifications, name='unread_notifications'),
    path('read/<int:notification_id>/', views.read_and_redirect, name='read_and_redirect'),
]


