# notification/admin.py

from django.contrib import admin
from .models import Notification, NotificationRecipient
from school.models import Student

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    filter_horizontal = ('classrooms',)  # Se você usa ManyToMany para turmas
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Distribuir para usuários
        users_set = set()
        
        # Usuários das turmas
        for turma in obj.classrooms.all():
            alunos = Student.objects.filter(classes_assigned=turma)
            users_set.update(aluno.user for aluno in alunos if aluno.user)
        
        # Se quiser adicionar outros usuários diretamente, você pode adaptar
        
        # Criar NotificationRecipient para cada usuário, evitando duplicatas
        for user in users_set:
            NotificationRecipient.objects.get_or_create(notification=obj, user=user)
