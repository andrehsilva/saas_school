from django.contrib import admin
from .models import Note

from django.urls import reverse

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'subject', 'title', 'evaluation_period', 'score', 'weight', 'date', 'created_at'
    )
    list_filter = ('subject', 'date', 'student', 'evaluation_period')
    search_fields = (
        'student__user__username', 
        'subject__name', 
        'title', 
        'performance',
        'evaluation_period',
        'score',
        'attachment',
    )
    list_editable = ('score', 'weight')
    date_hierarchy = 'date'
    ordering = ('-date', '-created_at')

    fieldsets = (
        (None, {
            'fields': ('student', 'subject', 'title', 'date', 'evaluation_period','attachment')
        }),
        ('Conteúdo', {
            'fields': ('description', 'performance'),
            'classes': ('collapse',)
        }),
        ('Avaliação', {
            'fields': ('score', 'weight'),
            'classes': ('wide',)
        }),
    )

    