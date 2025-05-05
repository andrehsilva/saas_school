# books/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_documents, name='my_documents'),
    path('document/<int:doc_id>/view/', views.view_pdf, name='view_pdf'),
]
