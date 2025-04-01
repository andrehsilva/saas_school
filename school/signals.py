from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Role

@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    """Cria os papéis padrão sempre que o app 'school' for migrado."""
    if sender.name == 'school':
        default_roles = ['Director', 'Coordinator', 'Teacher', 'Parent', 'Student']
        for role in default_roles:
            Role.objects.get_or_create(name=role)
