# notification/utils.py

from .models import Notification, NotificationRecipient
from school.models import Class, Student
from django.contrib.auth import get_user_model

User = get_user_model()

def send_notification(title, message, url=None, users=None, classes=None):
    """
    Envia uma notificação para usuários e/ou turmas específicas.
    """
    notification = Notification.objects.create(
        title=title,
        message=message,
        url=url
    )

    user_set = set()

    # Adiciona usuários individuais
    if users:
        user_set.update(users)

    # Adiciona usuários das turmas
    if classes:
        notification.classrooms.set(classes)
        for turma in classes:
            alunos = Student.objects.filter(classes_assigned=turma)
            user_set.update(aluno.user for aluno in alunos if aluno.user)

    # Cria NotificationRecipient para cada usuário
    for user in user_set:
        NotificationRecipient.objects.create(notification=notification, user=user)

    return notification
