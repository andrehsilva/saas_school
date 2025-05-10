from django.contrib import admin
from .models import Ticket, TicketMessage, TicketAllowedResponder

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'subject', 'parent', 'status', 'created_at']
    search_fields = ['ticket_number', 'subject', 'parent__user__username']
    list_filter = ['status', 'created_at']
    readonly_fields = ['ticket_number', 'created_at']

@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'sender', 'created_at']
    search_fields = ['ticket__ticket_number', 'sender__username']
    readonly_fields = ['created_at']

@admin.register(TicketAllowedResponder)
class TicketAllowedResponderAdmin(admin.ModelAdmin):
    list_display = ['user']
    search_fields = ['user__username', 'user__email']
