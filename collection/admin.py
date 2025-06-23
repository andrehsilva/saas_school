from django.contrib import admin
from django.utils.html import format_html
from .models import CollectionItem, Category
from notification.utils import send_notification, send_notification_to_class, send_notification_to_class_staff
from school.models import Class

@admin.register(CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'html_path', 'preview', 'uploaded_by', 'uploaded_at')
    search_fields = ('title', 'description', 'html_path')
    list_filter = ('uploaded_at', 'categories', 'target_grades', 'target_classes')
    filter_horizontal = ('categories', 'target_grades', 'target_classes', 'target_users')

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'html_path', 'thumbnail')
        }),
        ('Relacionamentos', {
            'fields': ('categories', 'target_grades', 'target_classes', 'target_users')
        }),
        ('Metadados', {
            'fields': ('uploaded_by',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

        notified_ids = set()

        # URL opcional - substitua pela rota certa se houver uma view_detail
        item_url = f"/collection/item/{obj.id}/"

        # 🔔 Usuários diretos
        for user in obj.target_users.all():
            if user.id not in notified_ids:
                send_notification(
                    recipients=user,
                    title=f"Novo item publicado: {obj.title}",
                    message=obj.description or "",
                    url=item_url
                )
                notified_ids.add(user.id)

        # 🔔 Classes
        for turma in obj.target_classes.all():
            send_notification_to_class(
                turma,
                title=f"Novo item publicado: {obj.title}",
                message=obj.description or "",
                url=item_url
            )
            send_notification_to_class_staff(
                turma,
                title=f"Novo item publicado: {obj.title}",
                message=obj.description or "",
                url=item_url
            )

        # 🔔 Séries
        for grade in obj.target_grades.all():
            for turma in Class.objects.filter(grade=grade):
                send_notification_to_class(
                    turma,
                    title=f"Novo item publicado: {obj.title}",
                    message=obj.description or "",
                    url=item_url
                )
                send_notification_to_class_staff(
                    turma,
                    title=f"Novo item publicado: {obj.title}",
                    message=obj.description or "",
                    url=item_url
                )

    def preview(self, obj):
        if obj.html_path:
            return format_html('<a href="{}" target="_blank">Visualizar HTML</a>', obj.html_path)
        return "Sem HTML"
    
    def view_link(self, obj):
        return format_html('<a href="/collection/item/{}/" target="_blank">Abrir</a>', obj.id)
        view_link.short_description = "Acesso Direto"

        list_display += ('view_link',)

    preview.short_description = "Pré-visualização"

admin.site.register(Category)
