from django.contrib import admin
from django.urls import reverse
from .models import Message, MessageType, ReceivedMessage, Event

from school.models import Class, Student, Grade
from django.urls import reverse
from django.http import HttpResponseRedirect

  
class MessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'created_by', 'get_classes', 'get_users', 'type')
    list_filter = ('created_at', 'type')
    search_fields = ('title', 'context')
    list_editable = ('type',)

    def get_classes(self, obj):
        return ", ".join([cls.name for cls in obj.classes.all()])
    get_classes.short_description = 'Turmas'

    def get_users(self, obj):
        return ", ".join([user.username for user in obj.users.all()])
    get_users.short_description = 'Usuários'

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        super().save_model(request, obj, form, change)

    


       

    def response_add(self, request, obj, post_url_continue=None):
        return HttpResponseRedirect(
            reverse('message:message_detail', args=[ obj.id])
        )
 


class MessageTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)


admin.site.register(MessageType, MessageTypeAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(ReceivedMessage)



class EventAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'inicio', 'fim', 'get_classes')
    list_filter = ('inicio',)
    search_fields = ('titulo',)
    filter_horizontal = ('classes',)
    date_hierarchy = 'inicio'
    ordering = ('-inicio',)

    fieldsets = (
        (("Informações do Evento"), {
            'fields': ('titulo', 'inicio', 'fim')
        }),
        (("Turmas Destinatárias"), {
            'fields': ('classes',)
        }),
    )

    def get_classes(self, obj):
        return ", ".join([cls.name for cls in obj.classes.all()])
    get_classes.short_description = ("Turmas")

    

admin.site.register(Event, EventAdmin)