from django.contrib import admin
from .models import Note
from django.urls import reverse
from notification.utils import send_notification
from school.models import Parent


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
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        if is_new:
            try:
                note_url = reverse('notes:note_detail', kwargs={'note_id': obj.id})
            except:
                note_url = f'/notes/{obj.id}/'

            # Aluno
            recipients = []
            if obj.student.user:
                recipients.append(obj.student.user)

            # Pais/Responsáveis
            parents = Parent.objects.filter(children=obj.student)
            recipients += [p.user for p in parents if p.user]

            send_notification(
                recipients=recipients,
                title=f"Nova nota em {obj.subject.name}",
                message=obj.title,
                url=note_url
            )
