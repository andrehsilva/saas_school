# navigation/admin.py
from django.contrib import admin
from .models import NavigationLink

@admin.register(NavigationLink)
class NavigationLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active',)
    verbose_name = "Link"
    verbose_name_plural = "Links"