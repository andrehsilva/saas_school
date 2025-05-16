# message/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import MessageType
from school.models import Role, Class



@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    if sender.name == 'school':
        default_roles = {
            'Director': {'can_post': True, 'description': 'Acesso completo de diretor'},
            'Coordinator': {'can_post': True, 'description': 'Coordenador de série'},
            'Teacher': {'can_post': True, 'description': 'Professor da turma'},
            'Parent': {'can_post': False, 'description': 'Responsável por aluno'},
            'Student': {'can_post': False, 'description': 'Estudante'}
        }

        for role_name, config in default_roles.items():
            try:
                role_obj, created = Role.objects.get_or_create(
                    name=role_name,
                    defaults=config
                )
                # Atualiza se já existe e há diferenças
                if not created and (role_obj.can_post != config['can_post'] or role_obj.description != config['description']):
                    role_obj.can_post = config['can_post']
                    role_obj.description = config['description']
                    role_obj.save()
            except Exception as e:
                print(f"Erro ao processar papel {role_name}: {str(e)}")

        # Garante valor padrão para classes (redundante se default=True no model)
        Class.objects.filter(is_regular__isnull=True).update(is_regular=True)