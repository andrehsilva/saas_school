from django.contrib import admin
from .models import Message, ReceivedMessage
from school.models import Class, Series
from django.contrib.auth.models import User
from django.utils.html import format_html

class ReceivedMessageInline(admin.TabularInline):
    model = ReceivedMessage
    extra = 0
    readonly_fields = ('recipient', 'received_at', 'read')


class MessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'sender', 'created_at', 'get_recipient_count', 'get_classes_and_series')
    search_fields = ('title', 'sender__username', 'description')
    list_filter = ('created_at', 'sender__groups')

    # Função para contar os destinatários
    def get_recipient_count(self, obj):
        count = obj.received_messages.count()  # Contagem de mensagens recebidas
        return format_html(f"<b>{count}</b>")
    get_recipient_count.short_description = "Número de Destinatários"

    # Função para exibir classes e séries associadas à mensagem
    def get_classes_and_series(self, obj):
        # Exibe turmas (classes) e séries associadas aos destinatários
        classes = obj.classes.all()
        series = obj.series.all()
        
        classes_list = ", ".join([cls.name for cls in classes])
        series_list = ", ".join([ser.name for ser in series])
        
        return format_html(f"<b>Classes:</b> {classes_list}<br><b>Séries:</b> {series_list}")
    get_classes_and_series.short_description = "Classes e Séries"

    # Exibir classes e séries na visualização de detalhes
    def view_on_site(self, obj):
        return None  # Desabilitar link para visualização no site

admin.site.register(Message, MessageAdmin)
admin.site.register(ReceivedMessage)