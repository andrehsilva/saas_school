from .models import Notification
from django.contrib.auth import get_user_model
from ticket.models import TicketAllowedResponder
User = get_user_model()



def get_ticket_staff_default(ticket):
    """
    Retorna um usuário staff com permissão para responder ao ticket.
    Por padrão, retorna o último que respondeu ou qualquer um autorizado.
    """
    # 1. Se o ticket já tem mensagens, pega o último respondente que não é o criador
    last_message = ticket.ticketmessage_set.order_by('-created_at').first()
    if last_message and last_message.sender != ticket.parent.user:
        return last_message.sender

    # 2. Se não tem mensagens, ou só o criador respondeu, pega alguém da lista de autorizados
    allowed = TicketAllowedResponder.objects.first()
    if allowed:
        return allowed.user

    # 3. Último recurso: pega qualquer staff
    return User.objects.filter(is_staff=True).first()

def send_notification(recipient=None, recipient_id=None, title="", message="", url=None):
    if recipient is None and recipient_id is not None:
        recipient = User.objects.get(id=recipient_id)
    elif recipient is not None:
        pass  # já é o usuário
    else:
        raise ValueError("É necessário informar recipient ou recipient_id")

    Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        url=url
    )
    print(f"Enviando notificação para")

