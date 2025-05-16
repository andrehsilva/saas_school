from django.db.models import Q
from .models import Message, ReceivedMessage
from school.models import Class, Grade, Student, Parent,GradeCoordinator
from django.utils import timezone

def get_user_visibility_context(user):
    students = Student.objects.filter(user=user)
    student_user_ids = [user.id]
    user_classes = Class.objects.none()
    user_grades = Grade.objects.none()

    # 1. Verifica se é Coordenador/Diretor (com designação ativa)
    is_coordinator = GradeCoordinator.objects.filter(
        user=user,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).exists()

    # 2. Verifica se é Diretor Global (permissão especial)
    is_global_director = user.has_perm('school.global_director_access')

    if is_coordinator or is_global_director:
        user_classes = Class.objects.all()
        user_grades = Grade.objects.all()
    else:
        # 3. Verifica se é Aluno/Responsável
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

        # 4. Verifica se é Professor
        if not user_classes.exists():
            user_classes = Class.objects.filter(teachers=user).distinct()

        # 5. Define as séries com base nas turmas
        user_grades = Grade.objects.filter(classrooms__in=user_classes).distinct()

    return {
        "students": students,
        "student_user_ids": student_user_ids,
        "user_classes": user_classes,
        "user_grades": user_grades,
    }



def get_visible_messages(user):
    context = get_user_visibility_context(user)

    # Mensagens diretas (para o usuário ou seus alunos)
    direct_messages = Message.objects.filter(
        Q(users=user) | Q(users__id__in=context["student_user_ids"])
    )

    # Mensagens para turmas do usuário
    class_messages = Message.objects.filter(classes__in=context["user_classes"])

    # Mensagens para séries do usuário (incluindo todas as turmas da série)
    grade_messages = Message.objects.filter(classes__grade__in=context["user_grades"])

    # Mensagens recebidas via ReceivedMessage
    received_messages = Message.objects.filter(received_by__recipient=user)

    # Combina todas as mensagens
    messages = (
        direct_messages | 
        class_messages | 
        grade_messages | 
        received_messages
    ).distinct()

    return messages