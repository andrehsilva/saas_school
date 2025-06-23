from django.contrib import admin
from .models import *
from django.utils.html import format_html

class CallToActionAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'btn_texto', 'active','preview_image')

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="50" style="object-fit: cover;"/>'.format(obj.image.url))
        return "Sem imagem"
    
    preview_image.short_description = "Pré-visualização"


class BlogAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_description', 'created', 'star','active','preview_image')
    list_editable = ('star', 'active')  # Permite edição direta na listagem
    list_filter = ('star', 'active', 'created')  # Filtros na lateral
    search_fields = ('name', 'description')  # Campo de busca

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="50" style="object-fit: cover;"/>'.format(obj.image.url))
        return "Sem imagem"
    
    preview_image.short_description = "Pré-visualização"


admin.site.register(CallToAction, CallToActionAdmin)
admin.site.register(Category)
admin.site.register(Blog,BlogAdmin)
