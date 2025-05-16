from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Message, ReceivedMessage, MessageType, MessageReadLog, Event
from school.models import Class, Grade, Student, Parent
from .utils import get_user_visibility_context, get_visible_messages
from django.core.exceptions import PermissionDenied
from .decorators import message_permission_required

@login_required
def messages_timeline(request):
    user = request.user
    
    # Obter contexto de visibilidade
    context = get_user_visibility_context(user)
    
    # Obter mensagens visíveis
    visible_messages = get_visible_messages(user)
    
    # Aplicar filtro de tipo
    selected_type = request.GET.get('type')
    if selected_type:
        visible_messages = visible_messages.filter(type_id=selected_type)
    
    # Aplicar busca
    search_query = request.GET.get('q', '')
    if search_query:
        visible_messages = visible_messages.filter(
            Q(title__icontains=search_query) |
            Q(context__icontains=search_query))
    
    # Ordenação e paginação
    visible_messages = visible_messages.order_by('-created_at')
    paginator = Paginator(visible_messages, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calcular mensagens não lidas
    read_messages = MessageReadLog.objects.filter(user=user).values_list('message_id', flat=True)
    unread_messages = visible_messages.exclude(id__in=read_messages)
    
    # Obter tipos de mensagem para filtro
    message_types = MessageType.objects.all()
    
    return render(request, 'message/messages_timeline.html', {
        'msgs': page_obj,
        'page_obj': page_obj,
        'message_types': message_types,
        'selected_type': selected_type,
        'unread_count': unread_messages.count(),
        'search_query': search_query,
    })

@login_required
def mark_as_read(request, message_id):
    user = request.user
    message = get_object_or_404(Message, id=message_id)
    
    if not MessageReadLog.objects.filter(user=user, message=message).exists():
        MessageReadLog.objects.create(user=user, message=message, read=True)
    
    return JsonResponse({"success": True})


@login_required
@message_permission_required
def message_detail(request, id):
    message = get_object_or_404(Message, id=id)
    user = request.user
    
    # Verificar se o usuário tem permissão para ver a mensagem
    has_permission = (
        # É o remetente
        message.created_by == user or
        # Está na lista de usuários destinatários
        message.users.filter(id=user.id).exists() or
        # Pertence a uma turma destinatária
        user.student.classes_assigned.filter(id__in=message.classes.values_list('id', flat=True)).exists()
    )
    
    if not has_permission:
        raise PermissionDenied("Você não tem permissão para visualizar esta mensagem")
    
    return render(request, 'message/message_detail.html', {'message': message})



@login_required
def event_json(request):
    user = request.user
    eventos = Event.objects.none()
    
    # Aluno
    try:
        student = Student.objects.get(user=user)
        turmas = student.classes_assigned.all()
        eventos = Event.objects.filter(classes__in=turmas)
    
    # Responsável
    except Student.DoesNotExist:
        try:
            parent = Parent.objects.get(user=user)
            filhos = parent.children.all()
            turmas = Class.objects.filter(students__in=filhos)
            eventos = Event.objects.filter(classes__in=turmas)
        
        # Professor/Coordenador/Diretor
        except Parent.DoesNotExist:
            turmas = Class.objects.filter(
                Q(teachers=user) | 
                Q(grade__coordinators=user)
            )
            eventos = Event.objects.filter(classes__in=turmas)
    
    # Formatar dados
    data = [{
        "title": evento.titulo,
        "start": evento.inicio.isoformat(),
        "end": evento.fim.isoformat() if evento.fim else None,
    } for evento in eventos.distinct()]
    
    return JsonResponse(data, safe=False)

def calendar_view(request):
    return render(request, 'message/calendar.html')