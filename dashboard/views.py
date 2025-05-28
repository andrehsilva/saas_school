from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .permissions import dashboard_access_required, role_required  # ajuste o nome se for diferente
from school.models import Grade, Class, Student, Parent, Subject, UserRole


@role_required(["Diretor", "Coordenador"])
def dashboard_home(request):
    user = request.user

    user_roles = user.roles.values_list('role__name', flat=True)
    context = {
        'is_director': 'Diretor' in user_roles,
        'is_coordinator': 'Coordenador' in user_roles,
        'is_teacher': 'Professor' in user_roles,
        'is_collaborator': 'Colaborador' in user_roles,
        'total_grades': Grade.objects.count(),
        'total_classes': Class.objects.count(),
        'total_teachers': UserRole.objects.filter(role__name='Professor').count(),
        'total_students': Student.objects.count(),
        'total_parents': Parent.objects.count(),
        'total_grades': Grade.objects.count(),
        'total_subjects': Subject.objects.count(),
        'my_posts': 0,  # Substitua conforme seu modelo de post
        'published_documents': 0,  # Substitua conforme seu modelo de documento
    }
    return render(request, "dashboard/home.html", context)

