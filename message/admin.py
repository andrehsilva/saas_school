from django.contrib import admin
from django.urls import reverse
from .models import Message, MessageType, ReceivedMessage, Event
from django.db.models import Q
from school.models import UserRole 
from school.models import Class, Student, Grade
# from django.http import HttpResponseRedirect # Importação não usada, pode ser removida se não houver outra função
from django.contrib.auth import get_user_model
from notification.utils import send_notification, send_notification_to_class


User = get_user_model()
  
class MessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'created_by', 'get_grades','get_classes', 'get_users', 'type')
    list_filter = ('created_at', 'type')
    search_fields = ('title', 'context')
    list_editable = ('type',)

    def get_classes(self, obj):
        return ", ".join([cls.name for cls in obj.classes.all()])
    get_classes.short_description = 'Turmas'

    def get_grades(self, obj):
        return ", ".join([cls.name for cls in obj.grades.all()])
    get_grades.short_description = 'Séries'

    def get_users(self, obj):
        return ", ".join([user.username for user in obj.users.all()])
    get_users.short_description = 'Usuários'

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        super().save_model(request, obj, form, change)

        # Gerar a URL da mensagem usando reverse()
        message_url = reverse('message:message_detail', kwargs={'id': obj.id})

        # Notificações para usuários individuais
        for user in obj.users.all():
            send_notification(
                recipients=user, # CORRIGIDO: de 'recipient' para 'recipients'
                title=obj.title,
                message=obj.context,
                url=message_url
            )

        # Notificações para turmas (esta chamada já está correta, pois send_notification_to_class
        # por sua vez chama send_notification com a lista de usuários extraída)
        for turma in obj.classes.all():
            send_notification_to_class(
                turma,
                title=obj.title,
                message=obj.context,
                url=message_url
            )
        
        for grade in obj.grades.all():
            for turma in Class.objects.filter(grade=grade):
                send_notification_to_class(
                    turma,
                    title=obj.title,
                    message=obj.context,
                    url=message_url
                )


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "created_by":
            allowed_roles = ['Diretor', 'Coordenador', 'Colaborador', 'Professor']
            excluded_roles = ['Aluno', 'Pai']
            
            kwargs["queryset"] = User.objects.filter(
                Q(roles__role__name__in=allowed_roles)
            ).exclude(
                Q(roles__role__name__in=excluded_roles)
            ).distinct().order_by('username')
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

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
