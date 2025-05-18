from django.db.models import Q
from .models import Message, ReceivedMessage
from school.models import Class, Grade, Student, Parent
from django.utils import timezone

def get_user_visibility_context(user):
    # Inicializa variáveis
    students = Student.objects.filter(user=user)
    student_user_ids = [user.id]
    user_classes = Class.objects.none()
    user_grades = Grade.objects.none()

    # Verifica se é Diretor Global ou tem cargos de coordenação/direção
    is_global_director = user.has_perm('school.global_director_access')
    coordinated_grades = Grade.objects.filter(
        Q(coordinators=user) | Q(directors=user))
    
    if is_global_director or coordinated_grades.exists():
        # Acesso total para diretores globais e gestores de série
        user_classes = Class.objects.all()
        user_grades = Grade.objects.all()
    else:
        # Lógica para outros usuários
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

        # Verifica se é professor
        if not user_classes.exists():
            user_classes = Class.objects.filter(teachers=user).distinct()

        # Obtém séries relacionadas
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

    # Monta a query de mensagens
    query = Q()
    
    # Mensagens diretas
    query |= Q(users=user) | Q(users__id__in=context["student_user_ids"])
    
    # Mensagens para turmas/séries
    if context["user_classes"].exists():
        query |= Q(classes__in=context["user_classes"])
    
    if context["user_grades"].exists():
        query |= Q(classes__grade__in=context["user_grades"])
    
    # Mensagens recebidas
    query |= Q(received_by__recipient=user)

    return Message.objects.filter(query).distinct().order_by('-created_at')