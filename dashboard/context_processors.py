def user_roles(request):
    user = request.user
    roles = set()
    if user.is_authenticated:
        roles = set(user.roles.values_list('role__name', flat=True))
    return {
        'is_director': 'Diretor' in roles,
        'is_coordinator': 'Coordenador' in roles,
        'is_teacher': 'Professor' in roles,
        'is_collaborator': 'Colaborador' in roles,
        'user_roles': roles,
    }