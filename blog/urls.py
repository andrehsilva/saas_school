from django.urls import path
from . import views
from .views import ListBlog, ArticleDetailView

app_name = 'blog'

urlpatterns = [
    path('', ListBlog.as_view(), name='blog'),
    path('article/<uuid:pk>/', ArticleDetailView.as_view(), name='article'),


    path('dashboard/blog/', views.dashboard_blog_list, name='dashboard_blog_list'),
    path('dashboard/blog/create/', views.dashboard_blog_create, name='dashboard_blog_create'),
    path('dashboard/blog/<uuid:pk>/', views.dashboard_blog_detail, name='dashboard_blog_detail'),
    path('dashboard/blog/<uuid:pk>/edit/', views.dashboard_blog_edit, name='dashboard_blog_edit'),
    path('dashboard/blog/<uuid:pk>/delete/', views.dashboard_blog_delete, name='dashboard_blog_delete'),


    path('dashboard/categories/', views.dashboard_category_list, name='dashboard_category_list'),
    path('dashboard/categories/create/', views.dashboard_category_create, name='dashboard_category_create'),
    path('dashboard/categories/<int:pk>/edit/', views.dashboard_category_edit, name='dashboard_category_edit'),
    path('dashboard/categories/<int:pk>/delete/', views.dashboard_category_delete, name='dashboard_category_delete'),
    
]