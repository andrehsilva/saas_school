# message/templatetags/role_tags.py
from django import template
from school.models import UserRole

register = template.Library()

@register.filter(name="has_role")
def has_role(user, role_names):
    if not user.is_authenticated:
        return False
        
    roles = role_names.split(",")
    return UserRole.objects.filter(
        user=user,
        role__name__in=[role.strip() for role in roles]
    ).exists()