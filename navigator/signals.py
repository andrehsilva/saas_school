# navigator/signals.py

from navigator.models import NavigationLink
from django.db.models.signals import post_migrate
from django.dispatch import receiver

DEFAULT_LINKS = [
    {'title': 'Home', 'url': '/', 'order': 1},
    {'title': 'Jogos/Coleções', 'url': '/collection/', 'order': 2},
    {'title': 'Meus Livros', 'url': '/books/', 'order': 3},
    {'title': 'Mensagens', 'url': '/message/messages/', 'order': 4},
    {'title': 'Tickets', 'url': '/ticket/', 'order': 5},
    {'title': 'Boletim', 'url': '/notes/', 'order': 6},
]

@receiver(post_migrate)
def create_default_navigator(sender, **kwargs):
    if sender.name == 'navigator':
        for link in DEFAULT_LINKS:
            try:
                NavigationLink.objects.get_or_create(
                    title=link['title'],
                    defaults={'url': link['url'], 'order': link['order']}
                )
            except Exception as e:
                import logging
                logging.error(f"Erro ao criar link de navegação: {e}")
