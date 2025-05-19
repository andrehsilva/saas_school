from django.contrib import admin
from .models import Ticket, TicketMessage, TicketAllowedResponder, TicketCategory


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'subject', 'parent', 'status', 'created_at']
    list_editable = ['status']
    search_fields = ['ticket_number', 'subject', 'parent__user__username']
    list_filter = ['status', 'created_at']
    readonly_fields = ['ticket_number', 'created_at']

    
@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'sender', 'created_at']
    search_fields = ['ticket__ticket_number', 'sender__username']
    readonly_fields = ['created_at']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(TicketAllowedResponder)
class TicketAllowedResponderAdmin(admin.ModelAdmin):
    list_display = ['user']
    search_fields = ['user__username', 'user__email']
    verbose_name = "Usuário com permissão"
    verbose_name_plural = "Usuários com permissões"

admin.site.register(TicketCategory)
