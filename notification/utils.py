from .models import Notification
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from school.models import Class
from message.utils import get_user_visibility_context

User = get_user_model()

def send_notification(recipients, title, message, url=None):
    if not isinstance(recipients, list):
        recipients = [recipients]

    print(f"DEBUG: send_notification chamado. Recebidos {len(recipients)} destinatários para '{title}'.")

    if not recipients:
        print("DEBUG: Lista de destinatários está vazia. Nenhuma notificação será criada.")
        return

    for user in recipients:
        if not user or not isinstance(user, User):
            print(f"ERRO: Destinatário inválido '{user}'. Deve ser uma instância de User. Pulando notificação para este.")
            continue

        # Verifica se já existe notificação idêntica nos últimos 10 minutos
        exists = Notification.objects.filter(
            recipient=user,
            title=title,
            message=message,
            url=url,
            created_at__gte=timezone.now() - timedelta(minutes=10)
        ).exists()

        if exists:
            print(f"AVISO: Notificação duplicada detectada para '{user.username}'. Ignorada.")
            continue

        try:
            Notification.objects.create(
                recipient=user,
                title=title,
                message=message,
                url=url
            )
            print(f"DEBUG: Notificação criada com sucesso para usuário '{user.username}' (ID: {user.id}).")
        except Exception as e:
            print(f"ERRO CRÍTICO: Falha ao criar notificação no banco de dados para '{user.username}': {e}")


def send_notification_to_class(class_instance, title, message, url=None):
    print(f"DEBUG: send_notification_to_class chamado para turma '{class_instance.name}' (ID: {class_instance.id}).")
    students = class_instance.students.all()
    users = [s.user for s in students if hasattr(s, 'user') and s.user]

    if not users:
        print(f"AVISO: Nenhum usuário válido encontrado para a turma '{class_instance.name}'. Notificação não enviada.")
        return

    send_notification(users, title, message, url)


def send_notification_to_class_staff(class_instance, title, message, url=None):
    print(f"DEBUG: send_notification_to_class_staff chamado para turma '{class_instance.name}' (ID: {class_instance.id}).")
    users = set()

    # Professores da turma
    users.update(class_instance.teachers.all())

    # Coordenadores/Diretores da série
    if class_instance.grade:
        users.update(class_instance.grade.coordinators.all())
        users.update(class_instance.grade.directors.all())

    if not users:
        print(f"AVISO: Nenhum professor/coordenador/diretor encontrado para turma '{class_instance.name}'.")
        return

    send_notification(list(users), title, message, url)


def get_user_notifications(user):
    try:
        context = get_user_visibility_context(user)
    except Exception as e:
        print(f"ERRO: Falha ao obter o contexto de visibilidade do usuário {user.username}: {e}")
        context = {"student_user_ids": []}

    recipient_ids = [user.id]
    if "student_user_ids" in context and isinstance(context["student_user_ids"], list):
        valid_student_ids = [uid for uid in context["student_user_ids"] if isinstance(uid, int)]
        recipient_ids.extend(valid_student_ids)

    print(f"DEBUG: Buscando notificações para os IDs de usuário: {recipient_ids}")

    return Notification.objects.filter(
        recipient_id__in=recipient_ids
    ).distinct().order_by('-created_at')
