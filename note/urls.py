from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    path('', views.notes_timeline, name='notes_timeline'),
    path('<int:note_id>/', views.note_detail, name='note_detail'),  # Nova rota
]