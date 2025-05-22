from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Message, MessageType, MessageReadLog, Event

from .utils import get_user_visibility_context, get_visible_messages



@login_required
def messages_timeline(request):
    user = request.user
    context = get_user_visibility_context(user)
    visible_messages = get_visible_messages(user)

    # Aplicar filtros
    selected_type = request.GET.get('type','').strip()
    search_query = request.GET.get('q', '')

    # Filtro por tipo
    if selected_type and selected_type.isdigit():
        visible_messages = visible_messages.filter(type_id=int(selected_type))

    # Filtro por texto (busca)
    if search_query:
        visible_messages = visible_messages.filter(
            Q(title__icontains=search_query) | 
            Q(context__icontains=search_query)
        )

    # Construir lista de itens
    all_items = [
        {"type": "message", "item": msg, "created_at": msg.created_at}
        for msg in visible_messages
    ]

    # Ordenar e paginar
    sorted_items = sorted(all_items, key=lambda x: x["created_at"], reverse=True)
    paginator = Paginator(sorted_items, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'message/messages_timeline.html', {
        'page_obj': page_obj,
        'message_types': MessageType.objects.all(),
        'selected_type': selected_type,
        'search_query': search_query,
    })





@login_required
def message_detail(request, id):
    queryset = get_visible_messages(request.user)
    message = get_object_or_404(queryset, id=id)

    return render(request, 'message/message_detail.html', {'message': message})




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