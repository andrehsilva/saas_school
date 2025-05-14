from django.contrib import admin
from .models import Note
from notification.utils import send_notification
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Envia notificação para todos os responsáveis (pais/mães) do aluno
        for parent in obj.student.parents.all():
            user = parent.user
            send_notification(
                    recipient=user,
                    title=f"Nova nota de {obj.subject.name}",
                    message=f"{obj.student.user.get_full_name() or obj.student.user.username} recebeu nota {obj.score} em \"{obj.title}\".",
                    url=reverse('notes:note_detail', args=[obj.id])  # Usar o namespace
                    
            )
