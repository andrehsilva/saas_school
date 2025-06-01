from django.urls import path
from .admin_views import import_users_view, export_users_view
from . import views


from django.urls import path, include

app_name = 'school' 

urlpatterns = [
    # ... outras rotas ...
    path('import-users/', import_users_view, name='import-users'),
    path('export-users/', export_users_view, name='export-users'),

    path('grades/', views.grade_list, name='grade_list'),
    path('grades/create/', views.grade_create, name='grade_create'),
    path('grades/<int:grade_id>/edit/', views.grade_edit, name='grade_edit'),
    path('grades/<int:grade_id>/delete/', views.grade_delete, name='grade_delete'),

    path('classes/<int:class_id>/usuarios/', views.class_users_view, name='class_users_view'),
    path('classes/<int:class_id>/usuarios/export/', views.class_users_export, name='class_users_export'),

    path('classes/', views.class_list, name='class_list'),
    path('classes/create/', views.class_create, name='class_create'),
    path('classes/<int:class_id>/edit/', views.class_edit, name='class_edit'),
    path('classes/<int:class_id>/delete/', views.class_delete, name='class_delete'),


    
]

