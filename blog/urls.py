from django.urls import path
from . import views
from .views import ListBlog, ArticleDetailView

app_name = 'blog'

urlpatterns = [
    path('', ListBlog.as_view(), name='blog'),
    path('article/<uuid:pk>/', ArticleDetailView.as_view(), name='article'),


    path('dashboard/blog/', views.dashboard_blog_list, name='dashboard_blog_list'),
    path('dashboard/blog/create/', views.dashboard_blog_create, name='dashboard_blog_create'),
    path('dashboard/blog/<int:pk>/', views.dashboard_blog_detail, name='dashboard_blog_detail'),
    path('dashboard/blog/<int:pk>/edit/', views.dashboard_blog_edit, name='dashboard_blog_edit'),
    path('dashboard/blog/<int:pk>/delete/', views.dashboard_blog_delete, name='dashboard_blog_delete'),
]