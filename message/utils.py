from django.db.models import Q
from .models import Message, ReceivedMessage
from school.models import Class, Grade, Student, Parent

def get_user_visibility_context(user):
    """
    Retorna os estudantes relacionados ao usuário, turmas e séries associadas.
    """
    students = Student.objects.filter(user=user)
    student_user_ids = [user.id]
    user_classes = Class.objects.none()
    user_grades = Grade.objects.none()

    # Se for aluno ou responsável
    if students.exists():
        user_classes = Class.objects.filter(students__in=students).distinct()
    else:
        try:
            parent = Parent.objects.get(user=user)
            students = parent.children.all()
            student_user_ids = list(students.values_list('user__id', flat=True))
            user_classes = Class.objects.filter(students__in=students).distinct()
        except Parent.DoesNotExist:
            pass

    # Se for professor (verifica através das turmas que leciona)
    if not user_classes.exists():
        user_classes = Class.objects.filter(teachers=user).distinct()

    # Se for coordenador/diretor (adaptar conforme seu modelo de permissões)
    if user.groups.filter(name__in=['Coordinator', 'Director']).exists():
        user_classes = Class.objects.all()

    user_grades = Grade.objects.filter(class__in=user_classes).distinct()

    return {
        "students": students,
        "student_user_ids": student_user_ids,
        "user_classes": user_classes,
        "user_grades": user_grades,
    }

def get_visible_messages(user):
    """
    Retorna todas as mensagens visíveis ao usuário.
    """
    context = get_user_visibility_context(user)

    direct_messages = Message.objects.filter(Q(users=user) | Q(users__id__in=context["student_user_ids"]))
    class_messages = Message.objects.filter(classes__in=context["user_classes"])
    grade_messages = Message.objects.filter(classes__grade__in=context["user_grades"])
    received_messages = Message.objects.filter(received_by__recipient=user)

    messages = (direct_messages | class_messages | grade_messages | received_messages).distinct()
    return messages
