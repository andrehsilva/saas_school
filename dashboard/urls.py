from django.urls import path
from .views import dashboard_home
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard_home, name='home'),
    path('users/import/', views.dashboard_import_users, name='import_users'),
    path('users/export/', views.dashboard_export_users, name='export_users'),
    # outras urls
]