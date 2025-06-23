from django.contrib import admin
from .models import Document, Category, ReceivedDocument
from django.utils.html import format_html
from django.urls import reverse
from notification.utils import send_notification, send_notification_to_class, send_notification_to_class_staff
from school.models import Class

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at', 'get_target_users', 'get_target_classes', 'get_target_grades','image')
    search_fields = ('title',)
    list_filter = ('uploaded_at',)

    def get_target_users(self, obj):
        return ", ".join([user.username for user in obj.target_users.all()])
    get_target_users.short_description = 'Usuários'

    def get_target_classes(self, obj):
        return ", ".join([class_obj.name for class_obj in obj.target_classes.all()])
    get_target_classes.short_description = 'Turmas'

    def get_target_grades(self, obj):
        return ", ".join([grade.name for grade in obj.target_grades.all()])
    get_target_grades.short_description = 'Séries'

    def image(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="100" height="50" style="object-fit: cover;"/>'.format(obj.thumbnail.url))
        return "Sem imagem"
    image.short_description = "Pré-visualização"

    def save_model(self, request, obj, form, change):
        obj.uploaded_by = request.user  # opcional, se usar este campo
        super().save_model(request, obj, form, change)

        def notify():
            try:
                url = reverse('books:document_detail', kwargs={'pk': obj.id})
            except:
                url = f'/books/{obj.id}/'

            # Usuários diretos
            for user in obj.target_users.all():
                send_notification(user, obj.title, "Novo documento publicado para você.", url)

            # Turmas
            for turma in obj.target_classes.all():
                send_notification_to_class(turma, obj.title, "Novo documento publicado para sua turma.", url)
                send_notification_to_class_staff(turma, obj.title, "Novo documento publicado para sua turma.", url)

            # Séries
            for grade in obj.target_grades.all():
                for turma in Class.objects.filter(grade=grade):
                    send_notification_to_class(turma, obj.title, "Novo documento publicado para sua série.", url)
                    send_notification_to_class_staff(turma, obj.title, "Novo documento publicado para sua série.", url)

        form.save_m2m()
        notify()

admin.site.register(Document, DocumentAdmin)
