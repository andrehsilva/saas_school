# message/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import MessageType

@receiver(post_migrate)
def create_default_message_types(sender, **kwargs):
    """Cria os tipos de mensagem padrão após a migração."""
    if sender.name == 'message':
        default_types = [
            'Pedagógica',
            'Dia-a-dia', 
            'Informativa', 
            'Evento', 
            'Atenção/Comunicado Importante', 
            'Saúde/Enfermaria', 
            'Cultural e Social', 
            'Feedback de Pais/Entrevistas', 
            'Reconhecimento e Premiações'
        ]
        for type_name in default_types:
            MessageType.objects.get_or_create(name=type_name)
