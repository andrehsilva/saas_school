from django.db.models import Q
from .models import Message, ReceivedMessage
from school.models import Class, Grade, Student, Parent

def get_user_visibility_context(user):
    students = Student.objects.filter(user=user)
    student_user_ids = [user.id]
    user_classes = Class.objects.none()
    user_grades = Grade.objects.none()

    is_global_director = user.has_perm('school.global_director_access')
    coordinated_grades = Grade.objects.filter(
        Q(coordinators=user) | Q(directors=user)
    )
    if is_global_director:
        # Diretor global tem acesso completo
        user_classes = Class.objects.all()
        user_grades = Grade.objects.all()
    elif coordinated_grades.exists():
        # Coordenadores/diretores só acessam suas próprias séries
        user_grades = coordinated_grades
        user_classes = Class.objects.filter(grade__in=user_grades)
    else:
        # Lógica para alunos, pais e professores
        if students.exists():
            user_classes = Class.objects.filter(students__in=students).distinct()
        else:
            try:
                parent = Parent.objects.get(user=user)
                children = parent.children.all()
                student_user_ids = list(children.values_list('user__id', flat=True))
                user_classes = Class.objects.filter(students__in=children).distinct()
            except Parent.DoesNotExist:
                pass

        if not user_classes.exists():
            user_classes = Class.objects.filter(teachers=user).distinct()

        user_grades = Grade.objects.filter(classrooms__in=user_classes).distinct()

    return {
        "students": students,
        "student_user_ids": student_user_ids,
        "user_classes": user_classes,
        "user_grades": user_grades,
        "is_global_director": is_global_director,
        "has_coordination_role": coordinated_grades.exists()
    }

def get_visible_messages(user):
    context = get_user_visibility_context(user)
    query = Q()

    # Mensagens CRIADAS pelo usuário (remetente)
    query |= Q(created_by=user)  # Nova condição adicionada
    
    # Mensagens diretas ao usuário ou seus dependentes
    query |= Q(users=user) | Q(users__id__in=context["student_user_ids"])
    
    # Mensagens para turmas do usuário
    if context["user_classes"].exists():
        query |= Q(classes__in=context["user_classes"])
    
    # Mensagens para séries do usuário (apenas as que ele tem acesso)
    if context["user_grades"].exists():
        query |= Q(grades__in=context["user_grades"])
    
    # Mensagens recebidas via ReceivedMessage
    query |= Q(received_by__recipient=user)

    return Message.objects.filter(query).distinct().order_by('-created_at')