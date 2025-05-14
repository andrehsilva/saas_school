from django.contrib import admin
from .models import Ticket, TicketMessage, TicketAllowedResponder, TicketCategory
from notification.utils import send_notification  # <- corrigido aqui

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'subject', 'parent', 'status', 'created_at']
    list_editable = ['status']
    search_fields = ['ticket_number', 'subject', 'parent__user__username']
    list_filter = ['status', 'created_at']
    readonly_fields = ['ticket_number', 'created_at']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Envia notificação se o ticket for alterado e tiver usuário responsável
        if obj.parent and obj.parent.user:
            send_notification(
                recipient=obj.parent.user,
                title=f"Atualização no ticket #{obj.ticket_number}",
                message=f"O status do ticket \"{obj.subject}\" foi alterado para \"{obj.status}\" pelo administrador.",
                url=f"/ticket/{obj.id}/"  # ou use reverse() para gerar URL
            )

@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'sender', 'created_at']
    search_fields = ['ticket__ticket_number', 'sender__username']
    readonly_fields = ['created_at']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Envia notificação para o usuário responsável, se houver
        if obj.ticket.parent and obj.ticket.parent.user:
            send_notification(
                recipient=obj.ticket.parent.user,
                title=f"Nova mensagem no ticket #{obj.ticket.ticket_number}",
                message=obj.message[:100],  # Primeiras 100 letras
                url=f"/ticket/{obj.ticket.id}/"
            )

@admin.register(TicketAllowedResponder)
class TicketAllowedResponderAdmin(admin.ModelAdmin):
    list_display = ['user']
    search_fields = ['user__username', 'user__email']
    verbose_name = "Usuário com permissão"
    verbose_name_plural = "Usuários com permissões"

admin.site.register(TicketCategory)
