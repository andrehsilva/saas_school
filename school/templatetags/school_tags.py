from django import template
from school.models import UserRole

register = template.Library()

@register.simple_tag
def has_dashboard_access(user):
    if not user.is_authenticated:
        return False
    allowed_roles = ['Diretor', 'Coordenador', 'Professor', 'Colaborador']
    user_roles = UserRole.objects.filter(user=user).select_related("role")
    user_role_names = [ur.role.name for ur in user_roles]
    return any(role in allowed_roles for role in user_role_names)