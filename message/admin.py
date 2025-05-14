from django.contrib import admin
from .models import Message, MessageType, ReceivedMessage
from notification.utils import send_notification
from django.urls import reverse

class MessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'created_by', 'get_classes', 'get_users', 'type')
    list_filter = ('created_at', 'type')
    search_fields = ('title', 'context')
    list_editable = ('type',)

    def get_classes(self, obj):
        return ", ".join([cls.name for cls in obj.classes.all()])
    get_classes.short_description = 'Classes'

    def get_users(self, obj):
        return ", ".join([user.username for user in obj.users.all()])
    get_users.short_description = 'Usuários'

    def save_model(self, request, obj, form, change):
        # Salva a mensagem
        super().save_model(request, obj, form, change)

        # Envia notificação para todos os usuários relacionados à mensagem
        for user in obj.users.all():  # Aqui consideramos que 'users' está relacionado corretamente
            send_notification(
                recipient=user,
                title=f"Nova mensagem: {obj.title}",
                message=f"Você recebeu uma nova mensagem de {obj.created_by.get_full_name() or obj.created_by.username}: \"{obj.title}\".",
                url=reverse('message:message_detail', args=[obj.id])  # Ajuste o nome da URL conforme necessário
            )

class MessageTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')  # Exibe a cor na lista
    search_fields = ('name',)

admin.site.register(MessageType, MessageTypeAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(ReceivedMessage)
