# school/urls.py
from django.urls import path
from .admin_views import export_users_view

urlpatterns = [
    path('admin/export-users/', export_users_view, name='export-users'),
]