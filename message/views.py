from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Message, ReceivedMessage, MessageType, MessageReadLog, Event
from notification.models import Notification, NotificationRecipient
from school.models import Class, Grade, Student, Parent
from .utils import get_user_visibility_context, get_visible_messages
from django.core.exceptions import PermissionDenied
from .decorators import message_permission_required


@login_required
def messages_timeline(request):
    user = request.user
    context = get_user_visibility_context(user)
    
    # Mensagens tradicionais (CORREÇÃO AQUI)
    visible_messages = get_visible_messages(user)  # Definindo a variável
    
    # Notificações
    notifications = Notification.objects.filter(
        Q(recipients=user) |
        Q(classrooms__in=context["user_classes"])
    ).distinct().order_by('-created_at')
    
    # Combinação e ordenação
    all_items = list(visible_messages) + list(notifications)
    sorted_items = sorted(all_items, key=lambda x: x.created_at, reverse=True)
    
    # Paginação
    paginator = Paginator(sorted_items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Cálculo de não lidos (CORREÇÃO AQUI)
    read_messages = MessageReadLog.objects.filter(user=user).values_list('message_id', flat=True)
    unread_messages_count = visible_messages.exclude(id__in=read_messages).count()  # Usando a variável definida
    
    read_notifications = NotificationRecipient.objects.filter(user=user, is_read=True).values_list('notification_id', flat=True)
    unread_notifications_count = notifications.exclude(id__in=read_notifications).count()
    
    unread_count = unread_messages_count + unread_notifications_count
    
    # Filtros
    message_types = MessageType.objects.all()
    selected_type = request.GET.get('type')
    search_query = request.GET.get('q', '')
    
    return render(request, 'message/messages_timeline.html', {
        'page_obj': page_obj,
        'message_types': message_types,
        'selected_type': selected_type,
        'unread_count': unread_count,
        'search_query': search_query,
    })

@login_required
def mark_as_read(request, item_type, item_id):
    user = request.user
    response = {"success": False}
    
    if item_type == 'message':
        message = get_object_or_404(Message, id=item_id)
        if not MessageReadLog.objects.filter(user=user, message=message).exists():
            MessageReadLog.objects.create(user=user, message=message, read=True)
            response["success"] = True
            
    elif item_type == 'notification':
        notification = get_object_or_404(Notification, id=item_id)
        NotificationRecipient.objects.update_or_create(
            user=user,
            notification=notification,
            defaults={'is_read': True}
        )
        response["success"] = True
    
    return JsonResponse(response)

@login_required
def message_detail(request, id, item_type):
    if item_type == 'message':
        item = get_object_or_404(Message, id=id)
        template = 'message/message_detail.html'
        
        # Verificação de permissão original
        has_permission = (
            item.created_by == request.user or
            item.users.filter(id=request.user.id).exists() or
            request.user.student.classes_assigned.filter(id__in=item.classes.values_list('id', flat=True)).exists()
        )
        
    elif item_type == 'notification':
        item = get_object_or_404(Notification, id=id)
        template = 'notification/notification_detail.html'
        
        # Verificação de permissão para notificação
        has_permission = (
            item.recipients.filter(id=request.user.id).exists() or
            item.classrooms.filter(id__in=request.user.student.classes_assigned.values_list('id', flat=True)).exists()
        )
    
    if not has_permission:
        raise PermissionDenied("Você não tem permissão para visualizar este conteúdo")
    
    return render(request, template, {item_type: item})



@login_required
def event_json(request):
    user = request.user
    context = get_user_visibility_context(user)  # Usando o contexto centralizado
    
    # Obter eventos baseados nas turmas do contexto
    eventos = Event.objects.filter(classes__in=context["user_classes"])
    
    # Formatar dados
    data = [{
        "title": evento.titulo,
        "start": evento.inicio.isoformat(),
        "end": evento.fim.isoformat() if evento.fim else None,
    } for evento in eventos.distinct()]
    
    return JsonResponse(data, safe=False)

def calendar_view(request):
    return render(request, 'message/calendar.html')