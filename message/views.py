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

    # Verificar se o usuário logado é um estudante
    student = Student.objects.filter(user=user).first()

    # Se não for estudante, verificar se é responsável por algum estudante
    if not student:
        try:
            parent = Parent.objects.get(user=user)  # Obtém a instância de Parent
            students = parent.children.all()  # Buscar os filhos
        except Parent.DoesNotExist:
            students = Student.objects.none()
    else:
        students = [student]

    # Converter estudantes para usuários
    student_users = students.values_list('user', flat=True)

    # Buscar turmas e séries associadas aos estudantes encontrados
    user_classes = Class.objects.filter(students__in=students).distinct()
    user_grades = Grade.objects.filter(class__in=user_classes).distinct()

    # Buscar mensagens diretas para o usuário e para os filhos do usuário (se for responsável)
    direct_messages = Message.objects.filter(Q(users=user) | Q(users__id__in=student_users))

    # Buscar mensagens associadas a turmas e séries dos filhos
    class_messages = Message.objects.filter(classes__in=user_classes)
    grade_messages = Message.objects.filter(classes__grade__in=user_grades)
    received_messages = Message.objects.filter(received_by__recipient=user)

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
