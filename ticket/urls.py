from django.urls import path
from . import views

app_name = 'ticket'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.create_ticket, name='create_ticket'),
    path('<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('<int:ticket_id>/fechar/', views.close_ticket, name='close_ticket'),


    path('tickets/', views.dashboard_ticket_list, name='dashboard_ticket_list'),
    path('tickets/<int:ticket_id>/', views.dashboard_ticket_detail, name='dashboard_ticket_detail'),
    path('dashboard/tickets/<int:ticket_id>/close/', views.dashboard_ticket_close, name='dashboard_ticket_close'),
    path('dashboard/tickets/<int:ticket_id>/reopen/', views.dashboard_ticket_reopen, name='dashboard_ticket_reopen'),

    path('dashboard/tickets/allowed-responders/', views.allowed_responders_list, name='allowed_responders_list'),
    path('dashboard/tickets/allowed-responders/create/', views.allowed_responder_create, name='allowed_responder_create'),
    path('dashboard/tickets/allowed-responders/<int:pk>/edit/', views.allowed_responder_edit, name='allowed_responder_edit'),
    path('dashboard/tickets/allowed-responders/<int:pk>/delete/', views.allowed_responder_delete, name='allowed_responder_delete'),

]