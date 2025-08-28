from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_collections, name='my_collections'),
    path('view/<int:item_id>/', views.view_html, name='view_html'),
]