from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Role, Class

# Signals
@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    """Cria os papéis padrão sempre que o app 'school' for migrado."""
    if sender.name == 'school':
        default_roles = {
            'Director': True,
            'Coordinator': True,
            'Teacher': True,
            'Parent': False,
            'Student': False
        }
        for role, can_post in default_roles.items():
            Role.objects.get_or_create(name=role, defaults={'can_post': can_post})

        # Garante que todas as classes criadas sejam regulares
        Class.objects.filter(is_regular__isnull=True).update(is_regular=True)    
