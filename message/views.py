from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
from .models import Message, ReceivedMessage, MessageType, MessageReadLog

from school.models import Class, Grade, Student, Parent
from django.contrib import messages as msg
from django.http import JsonResponse





@login_required
def messages_timeline(request):
    user = request.user
    print(f"\n[DEBUG] Usuário autenticado: {user.username} (ID: {user.id})")  # Debug 1
    
    try:
        # Verifica se é estudante
        student = Student.objects.get(user=user)
        print(f"[DEBUG] É estudante: {student}")  # Debug 2
        students = [student]
        student_user_ids = [user.id]
    except Student.DoesNotExist:
        print("[DEBUG] Não é estudante, verificando se é pai...")  # Debug 3
        try:
            parent = Parent.objects.get(user=user)
            print(f"[DEBUG] É pai/responsável: {parent}")  # Debug 4
            students = parent.children.all()
            student_user_ids = list(students.values_list('user__id', flat=True))
            print(f"[DEBUG] IDs dos filhos: {student_user_ids}")  # Debug 5
        except Parent.DoesNotExist:
            print("[DEBUG] Não é estudante nem pai")  # Debug 6
            students = Student.objects.none()
            student_user_ids = []

    # Debug adicional
    print(f"[DEBUG] Lista de estudantes: {students}")
    print(f"[DEBUG] IDs de usuários estudantes: {student_user_ids}")

    # Restante da sua lógica...
    user_classes = Class.objects.filter(students__in=students).distinct()
    user_grades = Grade.objects.filter(class__in=user_classes).distinct()

    # Debug das consultas
    print(f"[DEBUG] Turmas encontradas: {user_classes}")
    print(f"[DEBUG] Séries encontradas: {user_grades}")

    # Buscar mensagens diretas para o usuário e para os filhos do usuário (se for responsável)
    direct_messages = Message.objects.filter(Q(users=user) | Q(users__id__in=student_user_ids))

    # Buscar mensagens associadas a turmas e séries dos filhos
    class_messages = Message.objects.filter(classes__in=user_classes)
    grade_messages = Message.objects.filter(classes__grade__in=user_grades)
    received_messages = Message.objects.filter(received_by__recipient=user)

    # Debug final
    print("[DEBUG] Consultas executadas com sucesso")
    print(f" - Mensagens diretas: {direct_messages.count()}")
    print(f" - Mensagens por turma: {class_messages.count()}")
    print(f" - Mensagens por série: {grade_messages.count()}")


    # Unindo todas as mensagens sem duplicação
    msgs = (
        direct_messages | class_messages | grade_messages | received_messages
    ).distinct()

    # Filtro por tipo de mensagem
    selected_type = request.GET.get('type')
    if selected_type:
        msgs = msgs.filter(type_id=selected_type)

    # Ordenação das mensagens
    msgs = msgs.order_by('-created_at')

    # Obter todos os tipos de mensagens para o filtro
    message_types = MessageType.objects.all()


    # Buscar mensagens que já foram lidas pelo usuário
    read_messages = MessageReadLog.objects.filter(user=user).values_list('message_id', flat=True)

    # Filtrar mensagens não lidas
    unread_messages = msgs.exclude(id__in=read_messages)




    return render(request, 'message/messages_timeline.html', {
        'msgs': msgs,
        'message_types': message_types,
        'selected_type': selected_type,  
        'unread_count': unread_messages.count()# Para manter a seleção no template
        
    })


@login_required
def mark_as_read(request, message_id):
    user = request.user
    message = Message.objects.get(id=message_id)

    # Verificar se já foi marcado como lido
    if not MessageReadLog.objects.filter(user=user, message=message).exists():
        MessageReadLog.objects.create(user=user, message=message, read=True)

    return JsonResponse({"success": True})
