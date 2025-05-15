# message/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import MessageType



@receiver(post_migrate)
def create_default_message_types(sender, **kwargs):
    """Cria os tipos de mensagem padrão com cores após a migração."""
    if sender.name == 'message':
        default_types = {
            'Pedagógica': '#3498db',  # Azul
            'Dia-a-dia': '#2ecc71',  # Verde
            'Informativa': '#f1c40f',  # Amarelo
            'Evento': '#9b59b6',  # Roxo
            'Atenção/Comunicado Importante': '#e74c3c',  # Vermelho
            'Saúde/Enfermaria': '#1abc9c',  # Verde-água
            'Cultural e Social': '#e67e22',  # Laranja
            'Feedback de Pais/Entrevistas': '#95a5a6',  # Cinza
            'Reconhecimento e Premiações': '#ff69b4',  # Rosa
        }

        for type_name, color in default_types.items():
            MessageType.objects.get_or_create(name=type_name, defaults={'color': color})


