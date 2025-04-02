# message/admin.py
from django.contrib import admin
from .models import Message, MessageType

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

admin.site.register(Message, MessageAdmin)
admin.site.register(MessageType)

