from django.urls import path
from . import views
from .views import ListBlog, ArticleDetailView


urlpatterns = [
    path('', ListBlog.as_view(), name='blog'),
    path('article/<uuid:pk>/', ArticleDetailView.as_view(), name='article'),
]