from django.urls import path
from .admin_views import import_users_view, export_users_view

from django.urls import path, include

app_name = 'admin' 

urlpatterns = [
    # ... outras rotas ...
    path('import-users/', import_users_view, name='import-users'),
    path('export-users/', export_users_view, name='export-users'),
]

