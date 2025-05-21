from django.contrib import admin
from django.utils.html import format_html
from .models import CollectionItem, Category

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
    
    def get_classes(self, obj):
        return ", ".join([cls.name for cls in obj.classes.all()])
    get_classes.short_description = 'Classes'

    def get_users(self, obj):
        return ", ".join([user.username for user in obj.users.all()])
    get_users.short_description = 'Usuários'


    def preview(self, obj):
        if obj.html_path:
            # Concatena o caminho da URL do arquivo HTML com o URL base da mídia
            preview_url = obj.html_path
            return format_html('<a href="{}" target="_blank">Visualizar HTML</a>', preview_url)
        return "Sem HTML"
    preview.short_description = "Pré-visualização"

admin.site.register(Category)