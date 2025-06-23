from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [

    path('dashboard/notes/', views.dashboard_note_list, name='dashboard_note_list'),
    path('dashboard/notes/create/', views.dashboard_note_create, name='dashboard_note_create'),
    path('dashboard/notes/<int:note_id>/', views.dashboard_note_detail, name='dashboard_note_detail'),
    path('dashboard/notes/<int:note_id>/edit/', views.dashboard_note_edit, name='dashboard_note_edit'),
    path('dashboard/notes/<int:note_id>/delete/', views.dashboard_note_delete, name='dashboard_note_delete'),


    path('', views.notes_timeline, name='notes_timeline'),
    path('<int:note_id>/', views.note_detail, name='note_detail'),  # Nova rota
]