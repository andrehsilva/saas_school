from django.urls import path
from . import views  # Importação correta do módulo de views

app_name = "message"

# # message/urls.py (modificado)
# urlpatterns = [
#     #path("", views.messages_timeline, name="messages_timeline"),
#     path("<int:id>/", views.message_detail, name="message_detail"),
#     #path("calendar/", views.calendar_view, name="calendar"),
#     #path("event/json/", views.event_json, name="eventos_json"),

#     path('', views.message_list, name='message_list'),
#     path('create/', views.message_create, name='message_create'),
#     path('<int:message_id>/', views.message_detail, name='message_detail'),
#     path('<int:message_id>/edit/', views.message_edit, name='message_edit'),
#     path('<int:message_id>/delete/', views.message_delete, name='message_delete'),
#     path('<int:message_id>/mark-read/', views.mark_message_read, name='mark_message_read'),


# URLs para o dashboard (admin/gestão)
dashboard_urls = [
    path('dashboard/messages/', views.dashboard_message_list, name='dashboard_message_list'),
    path('dashboard/messages/create/', views.dashboard_message_create, name='dashboard_message_create'),
    path('dashboard/messages/<int:message_id>/', views.dashboard_message_detail, name='dashboard_message_detail'),
    path('dashboard/messages/<int:message_id>/edit/', views.dashboard_message_edit, name='dashboard_message_edit'),
    path('dashboard/messages/<int:message_id>/delete/', views.dashboard_message_delete, name='dashboard_message_delete'),
    path('dashboard/messages/<int:message_id>/mark-read/', views.dashboard_mark_message_read, name='dashboard_mark_message_read'),
    path('dashboard/events/create/', views.dashboard_event_create, name='dashboard_event_create'),
    path('dashboard/events/', views.dashboard_event_list, name='dashboard_event_list'),
    path('dashboard/events/<int:event_id>/edit/', views.dashboard_event_edit, name='dashboard_event_edit'),
    path('dashboard/events/<int:event_id>/delete/', views.dashboard_event_delete, name='dashboard_event_delete'),
    
]

# URLs para o parent (front-end para pais/responsáveis)
parent_urls = [
    path('messages/', views.parent_messages_timeline, name='parent_messages_timeline'),
    path('messages/<int:id>/', views.parent_message_detail, name='parent_message_detail'),
    path('calendar/', views.parent_calendar_view, name='parent_calendar_view'),
    path('parent/events/json/', views.parent_event_json, name='parent_event_json'),
    path('parent/calendar/', views.parent_calendar_view, name='parent_calendar_view'),
]

# Combinando todas as URLs
urlpatterns = dashboard_urls + parent_urls
