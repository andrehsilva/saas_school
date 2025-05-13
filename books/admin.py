# books/admin.py
from django.contrib import admin
from .models import Document, Category, ReceivedDocument
from django.utils.html import format_html

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

admin.site.register(Document, DocumentAdmin)

admin.site.register(Category)
admin.site.register(ReceivedDocument)
