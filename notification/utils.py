from .models import Notification
from django.contrib.auth import get_user_model
from school.models import Class
from message.utils import get_user_visibility_context # Certifique-se que este caminho está correto

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
            continue # Pula este recipient se não for um User válido

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
            # Em um ambiente de produção, você pode querer logar este erro em um sistema de log mais robusto.

def send_notification_to_class(class_instance, title, message, url=None):
    print(f"DEBUG: send_notification_to_class chamado para turma '{class_instance.name}' (ID: {class_instance.id}).")
    students = class_instance.students.all()
    
    # Certifique-se que 's.user' existe e é um objeto User válido
    users = []
    for s in students:
        if hasattr(s, 'user') and s.user: # Verifica se o objeto 's' tem um atributo 'user' e se ele não é None
            users.append(s.user)
        else:
            print(f"AVISO: Aluno '{s}' na turma '{class_instance.name}' não possui um usuário associado.")

    print(f"DEBUG: {len(users)} usuários extraídos da turma '{class_instance.name}' para notificação.")
    
    if not users:
        print(f"DEBUG: Nenhhum usuário válido encontrado para a turma '{class_instance.name}'. Notificação não enviada.")
        return

    # Chama a função send_notification com a lista de usuários extraída
    send_notification(users, title, message, url)

def get_user_notifications(user):
    # Certifique-se que get_user_visibility_context está implementado corretamente em message/utils.py
    # e retorna um dicionário com 'student_user_ids' sendo uma lista de IDs de usuários
    try:
        context = get_user_visibility_context(user)
    except Exception as e:
        print(f"ERRO: Falha ao obter o contexto de visibilidade do usuário {user.username}: {e}")
        context = {"student_user_ids": []} # Fallback para evitar erros

    recipient_ids = [user.id]
    if "student_user_ids" in context and isinstance(context["student_user_ids"], list):
        # Garante que todos os IDs são inteiros antes de estender
        valid_student_ids = [uid for uid in context["student_user_ids"] if isinstance(uid, int)]
        recipient_ids.extend(valid_student_ids)
    
    print(f"DEBUG: Buscando notificações para os IDs de usuário: {recipient_ids}")
    
    return Notification.objects.filter(
        recipient__id__in=recipient_ids
    ).order_by('-created_at')