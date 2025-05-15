from django.contrib import admin
from django.urls import reverse
from .models import Message, MessageType, ReceivedMessage, Event
from notification.utils import send_notification
from school.models import Class, Student, Grade


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

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        notified_users = set()

        # Notificar usuários selecionados diretamente
        for user in obj.users.all():
            if user not in notified_users:
                send_notification(
                    recipient=user,
                    title=f"Nova mensagem: {obj.title}",
                    message=f"Você recebeu uma nova mensagem de {obj.created_by.get_full_name() or obj.created_by.username}: \"{obj.title}\".",
                    url=reverse('message:message_detail', args=[obj.id])
                )
                notified_users.add(user)

        # Notificar alunos das turmas selecionadas
        for turma in obj.classes.all():
            for aluno in turma.students.all():
                if aluno.user not in notified_users:
                    send_notification(
                        recipient=aluno.user,
                        title=f"Mensagem para sua turma: {obj.title}",
                        message=f"Você recebeu uma nova mensagem enviada à turma {turma.name}.",
                        url=reverse('message:message_detail', args=[obj.id])
                    )
                    notified_users.add(aluno.user)

        # Notificar alunos das séries relacionadas às turmas
        grade_ids = obj.classes.values_list('grade_id', flat=True).distinct()
        grades = Grade.objects.filter(id__in=grade_ids)

        for grade in grades:
            for turma in grade.class_set.all():
                for aluno in turma.students.all():
                    if aluno.user not in notified_users:
                        send_notification(
                            recipient=aluno.user,
                            title=f"Mensagem para sua série: {obj.title}",
                            message=f"Você recebeu uma nova mensagem enviada para a série {grade.name}.",
                            url=reverse('message:message_detail', args=[obj.id])
                        )
                        notified_users.add(aluno.user)


class MessageTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)


admin.site.register(MessageType, MessageTypeAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(ReceivedMessage)
admin.site.register(Event)
