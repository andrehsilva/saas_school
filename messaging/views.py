from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Message, ReceivedMessage
from school.models import Class, Series

@login_required
def messages_timeline(request):
    user = request.user

    # Buscar mensagens que o usuário recebeu diretamente
    direct_messages = Message.objects.filter(individual_recipient=user)

    # Buscar as turmas e séries que o usuário está associado
    user_classes = Class.objects.filter(students=user)  # Turmas que o usuário (aluno) está matriculado
    user_series = Series.objects.filter(classes__in=user_classes)  # Séries associadas a essas turmas

    # Buscar mensagens destinadas a essas turmas e séries
    class_messages = Message.objects.filter(classes__in=user_classes)
    series_messages = Message.objects.filter(series__in=user_series)

    # Mensagens recebidas (usando o modelo ReceivedMessage)
    received_messages = ReceivedMessage.objects.filter(recipient=user).select_related('message')

    # Combinar todas as mensagens, removendo duplicatas
    messages = (
        direct_messages | class_messages | series_messages | Message.objects.filter(received_messages__recipient=user)
    ).distinct().order_by('-created_at')

    return render(request, 'messaging/messages_timeline.html', {'messages': messages})
