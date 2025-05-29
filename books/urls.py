# books/urls.py
from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.my_documents, name='my_documents'),
    path('<int:pk>/', views.document_detail, name='document_detail'),
    path('document/<int:doc_id>/view/', views.view_pdf, name='view_pdf'),

    path('dashboard/', views.dashboard_document_list, name='dashboard_document_list'),
    path('dashboard/<int:document_id>/', views.dashboard_document_detail, name='dashboard_document_detail'),
    path('dashboard/create/', views.dashboard_document_create, name='dashboard_document_create'),
    path('dashboard/<int:document_id>/edit/', views.dashboard_document_edit, name='dashboard_document_edit'),
]
