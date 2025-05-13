# ticket/signals.py

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import TicketCategory

@receiver(post_migrate)
def create_default_ticket_categories(sender, **kwargs):
    """Cria as categorias padrão de tickets após as migrações do app 'ticket'."""
    if sender.name == 'ticket':
        default_categories = [
            "Acadêmico/Pedagógico",
            "Matrículas e Secretaria",
            "Financeiro",
            "Comunicação com Responsáveis",
            "Transporte Escolar",
            "Alimentação Escolar",
            "Outros"
        ]

        for category in default_categories:
            TicketCategory.objects.get_or_create(name=category)
