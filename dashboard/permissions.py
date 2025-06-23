# dashboard/permissions.py
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from functools import wraps
from school.models import UserRole

def dashboard_access_required(view_func):
    """Verifica se o usuário tem permissão geral para acessar o dashboard"""
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        allowed_roles = ['Diretor', 'Coordenador', 'Professor', 'Colaborador']

        user_roles = UserRole.objects.filter(user=request.user).select_related("role")
        user_role_names = [ur.role.name for ur in user_roles]

        if any(role in allowed_roles for role in user_role_names):
            return view_func(request, *args, **kwargs)

        raise PermissionDenied("Você não tem permissão para acessar esta área.")
    
    return _wrapped_view


def role_required(allowed_roles):
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Busca todos os papéis do usuário
            user_roles = UserRole.objects.filter(user=user).select_related("role")
            user_role_names = [ur.role.name for ur in user_roles]

            # Verifica se pelo menos um papel bate
            if any(role in allowed_roles for role in user_role_names):
                return view_func(request, *args, **kwargs)

            raise PermissionDenied("Você não tem permissão para acessar esta página.")
        return _wrapped_view
    return decorator