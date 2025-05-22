from django.contrib import admin
from .models import Ticket, TicketMessage, TicketAllowedResponder, TicketCategory
from notification.utils import send_notification
from django.urls import reverse

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

        # Evita duplicações
        notified_users = set()

        # Gera a URL do ticket
        try:
            ticket_url = reverse('ticket_detail', args=[obj.ticket.id])
        except:
            ticket_url = f"/ticket/{obj.ticket.id}/"

        # Quando o remetente é o pai — notificar todos os autorizados daquela categoria
        if hasattr(obj.ticket, 'parent') and obj.ticket.parent.user == obj.sender:
            responders = TicketAllowedResponder.objects.filter(
                categories=obj.ticket.category
            ).select_related('user')

            for responder in responders:
                user = responder.user
                if user and user.id not in notified_users:
                    send_notification(
                        recipients=user,
                        title=f"Novo comentário no ticket: {obj.ticket.subject}",
                        message=obj.message,
                        url=ticket_url
                    )
                    notified_users.add(user.id)

        # Quando o remetente é da escola — notificar o pai
        else:
            if obj.ticket.parent and obj.ticket.parent.user:
                parent_user = obj.ticket.parent.user
                if parent_user.id not in notified_users:
                    send_notification(
                        recipients=parent_user,
                        title=f"Resposta ao seu ticket: {obj.ticket.subject}",
                        message=obj.message,
                        url=ticket_url
                    )
                    notified_users.add(parent_user.id)


@admin.register(TicketAllowedResponder)
class TicketAllowedResponderAdmin(admin.ModelAdmin):
    list_display = ['user']
    search_fields = ['user__username', 'user__email']
    verbose_name = "Usuário com permissão"
    verbose_name_plural = "Usuários com permissões"

admin.site.register(TicketCategory)
