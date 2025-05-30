"""
Views para o sistema de mensagens e eventos.
Organizado em duas seções:
1. Views do Dashboard (admin/gestão)
2. Views do Parent (front-end para pais/responsáveis)
"""

import json
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from .forms import EventForm  # Importe o formulário

from school.models import Grade, Class, Student, Parent, Role, UserRole
from dashboard.permissions import role_required
from notification.utils import (
    send_notification,
    send_notification_to_class,
    send_notification_to_class_staff
)
from message.models import Message, MessageType, ReceivedMessage, MessageReadLog, Event
from message.utils import get_user_visibility_context, get_visible_messages

# ---------------------------------------------------------------------
# HELPERS COMUNS
# ---------------------------------------------------------------------
def _get_message_url(message_obj):
    """Retorna a URL para visualização da mensagem"""
    try:
        return reverse('message:dashboard_message_detail', kwargs={'message_id': message_obj.id})
    except:
        return f'/dashboard/messages/{message_obj.id}/'

def _get_message_list_url():
    """Retorna a URL para a lista de mensagens"""
    try:
        return reverse('message:dashboard_message_list')
    except:
        return '/dashboard/messages/'

def get_message_types():
    """Retorna todos os tipos de mensagem disponíveis"""
    return MessageType.objects.all()

def get_eligible_recipients():
    """Retorna usuários, turmas e séries que podem receber mensagens"""
    users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    grades = Grade.objects.all().order_by('name')
    classes = Class.objects.all().order_by('name')

    return {
        'users': users,
        'grades': grades,
        'classes': classes
    }

def get_user_children(user):
    """Retorna os filhos do usuário (assumindo que existe um relacionamento Parent -> Student)"""
    try:
        # Busca a instância de Parent correspondente ao usuário
        parent = Parent.objects.get(user=user)
        # Filtra os Student usando a instância de Parent
        return Student.objects.filter(parents=parent)
    except Parent.DoesNotExist:
        return Student.objects.none()

# =============================================================================
# VIEWS DO DASHBOARD (ADMIN/GESTÃO)
# =============================================================================

@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_message_list(request):
    """
    Lista todas as mensagens que o usuário tem permissão para ver,
    com filtros e paginação.
    """
    # Filtros vindos da query string
    title = request.GET.get('title', '').strip()
    type_id = request.GET.get('type', '')
    created_by = request.GET.get('created_by', '')

    # Usuários com papéis administrativos podem ver todas as mensagens
    is_admin = request.user.roles.filter(role__name__in=["Diretor", "Coordenador", "Colaborador"]).exists()

    if is_admin:
        messages_qs = Message.objects.all()
    else:
        # Professores veem apenas mensagens que criaram ou que foram enviadas para eles
        messages_qs = Message.objects.filter(
            Q(created_by=request.user) |
            Q(users=request.user) |
            Q(classes__teachers=request.user) |
            Q(grades__in=Grade.objects.filter(
                Q(coordinators=request.user) |
                Q(directors=request.user) |
                Q(colaborator=request.user)
            ))
        ).distinct()

    # Aplicar filtros
    if title:
        messages_qs = messages_qs.filter(title__icontains=title)
    if type_id:
        messages_qs = messages_qs.filter(type_id=type_id)
    if created_by:
        messages_qs = messages_qs.filter(created_by_id=created_by)

    messages_qs = messages_qs.select_related('type', 'created_by').order_by('-created_at')

    # Paginação
    paginator = Paginator(messages_qs, 10)  # 10 mensagens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Preparar mensagens com permissões para o template
    messages_with_permissions = []
    for msg in page_obj.object_list:
        can_edit = is_admin or msg.created_by == request.user
        messages_with_permissions.append({
            'message': msg,
            'can_edit': can_edit
        })

    # Para os filtros
    message_types = MessageType.objects.all()
    users = User.objects.all()

    return render(request, 'dashboard/messages/list.html', {
        'messages_with_permissions': messages_with_permissions,
        'page_obj': page_obj,
        'message_types': message_types,
        'users': users,
        'current_title': title,
        'current_type': type_id,
        'current_created_by': created_by,
        'current_content': '',
        'current_users': [],
        'current_classes': [],
        'current_grades': []
    })

@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_message_create(request):
    """
    ✅ Criação de Mensagem
      - notifica todos os destinatários (usuários, turmas, séries) de forma genérica
    """
    recipients = get_eligible_recipients()
    message_types = get_message_types()

    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        type_id = request.POST.get('type')
        user_ids = request.POST.getlist('users')
        class_ids = request.POST.getlist('classes')
        grade_ids = request.POST.getlist('grades')

        if not title or not content:
            messages.error(request, "Título e conteúdo são obrigatórios.")
            return render(request, 'dashboard/messages/form.html', {
                'users': recipients['users'],
                'grades': recipients['grades'],
                'classes': recipients['classes'],
                'message_types': message_types,
                'current_title': title,
                'current_content': content,
                'current_type': type_id,
                'current_users': user_ids,
                'current_classes': class_ids,
                'current_grades': grade_ids,
                'form_title': "Nova Mensagem",
                'message': None
            })

        new_message = Message.objects.create(
            title=title,
            context=content,
            created_by=request.user,
            type_id=type_id if type_id else None
        )

        if 'image' in request.FILES:
            new_message.image = request.FILES['image']
        if 'attachments' in request.FILES:
            new_message.attachments = request.FILES['attachments']
        new_message.save()

        # Adiciona destinatários
        if user_ids:
            new_message.users.set(User.objects.filter(id__in=user_ids))
        if class_ids:
            new_message.classes.set(Class.objects.filter(id__in=class_ids))
        if grade_ids:
            new_message.grades.set(Grade.objects.filter(id__in=grade_ids))

        # --- NOTIFICAÇÕES SIMPLIFICADAS ---
        message_url = request.build_absolute_uri(reverse('message:parent_message_detail', args=[new_message.id]))
        notified_users = set()

        # Notificar todos os usuários selecionados diretamente
        for user in new_message.users.all():
            if user.id not in notified_users:
                send_notification(
                    recipients=user,
                    title=new_message.title,
                    message=new_message.context[:100] + "..." if len(new_message.context) > 100 else new_message.context,
                    url=message_url
                )
                notified_users.add(user.id)

        # Notificar alunos das turmas
        for turma in new_message.classes.all():
            for student in Student.objects.filter(classes_assigned=turma):
                if student.user and student.user.id not in notified_users:
                    ReceivedMessage.objects.create(
                        message=new_message,
                        recipient=student.user,
                        read=False
                    )
                    send_notification(
                        recipients=student.user,
                        title=new_message.title,
                        message=new_message.context[:100] + "..." if len(new_message.context) > 100 else new_message.context,
                        url=message_url
                    )
                    notified_users.add(student.user.id)

        # Notificar alunos das séries
        for grade in new_message.grades.all():
            for turma in Class.objects.filter(grade=grade):
                for student in Student.objects.filter(classes_assigned=turma):
                    if student.user and student.user.id not in notified_users:
                        ReceivedMessage.objects.create(
                            message=new_message,
                            recipient=student.user,
                            read=False
                        )
                        send_notification(
                            recipients=student.user,
                            title=new_message.title,
                            message=new_message.context[:100] + "..." if len(new_message.context) > 100 else new_message.context,
                            url=message_url
                        )
                        notified_users.add(student.user.id)

        messages.success(request, f"Mensagem '{new_message.title}' enviada com sucesso.")
        return redirect('message:dashboard_message_list')

    return render(request, 'dashboard/messages/form.html', {
        'users': recipients['users'],
        'grades': recipients['grades'],
        'classes': recipients['classes'],
        'message_types': message_types,
        'form_title': "Nova Mensagem",
        'current_title': '',
        'current_content': '',
        'current_type': '',
        'current_users': [],
        'current_classes': [],
        'current_grades': []
    })


@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_message_edit(request, message_id):
    """
    ✏️ Edição de Mensagem
      - atualiza mensagem e envia notificação genérica aos destinatários
    """
    message_obj = get_object_or_404(Message, id=message_id)

    if not (request.user == message_obj.created_by or request.user.roles.filter(role__name__in=["Diretor", "Coordenador", "Colaborador"]).exists()):
        raise PermissionDenied()

    recipients = get_eligible_recipients()
    message_types = get_message_types()

    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        type_id = request.POST.get('type')
        user_ids = request.POST.getlist('users')
        class_ids = request.POST.getlist('classes')
        grade_ids = request.POST.getlist('grades')

        if not title or not content:
            messages.error(request, "Título e conteúdo são obrigatórios.")
            return render(request, 'dashboard/messages/form.html', {
                'users': recipients['users'],
                'grades': recipients['grades'],
                'classes': recipients['classes'],
                'message_types': message_types,
                'current_title': title,
                'current_content': content,
                'current_type': type_id,
                'current_users': user_ids,
                'current_classes': class_ids,
                'current_grades': grade_ids,
                'form_title': "Editar Mensagem",
                'message': message_obj
            })

        # Atualiza os campos
        message_obj.title = title
        message_obj.context = content
        message_obj.type_id = type_id if type_id else None

        # Atualiza imagem e anexo, se enviados
        if 'image' in request.FILES:
            message_obj.image = request.FILES['image']
        if 'attachments' in request.FILES:
            message_obj.attachments = request.FILES['attachments']

        message_obj.save()

        # Atualiza destinatários
        message_obj.users.set(User.objects.filter(id__in=user_ids))
        message_obj.classes.set(Class.objects.filter(id__in=class_ids))
        message_obj.grades.set(Grade.objects.filter(id__in=grade_ids))

        # --- NOTIFICAÇÃO SIMPLIFICADA ---
        message_url = request.build_absolute_uri(reverse('message:parent_message_detail', args=[message_obj.id]))
        notified_users = set()

        # Notificar usuários diretos
        for user in message_obj.users.all():
            if user.id not in notified_users:
                send_notification(
                    recipients=user,
                    title="Mensagem Atualizada",
                    message=message_obj.title,
                    url=message_url
                )
                notified_users.add(user.id)

        # Notificar alunos das turmas
        for turma in message_obj.classes.all():
            for student in Student.objects.filter(classes_assigned=turma):
                if student.user and student.user.id not in notified_users:
                    send_notification(
                        recipients=student.user,
                        title="Mensagem Atualizada",
                        message=message_obj.title,
                        url=message_url
                    )
                    notified_users.add(student.user.id)

        # Notificar alunos das séries
        for grade in message_obj.grades.all():
            for turma in Class.objects.filter(grade=grade):
                for student in Student.objects.filter(classes_assigned=turma):
                    if student.user and student.user.id not in notified_users:
                        send_notification(
                            recipients=student.user,
                            title="Mensagem Atualizada",
                            message=message_obj.title,
                            url=message_url
                        )
                        notified_users.add(student.user.id)

        messages.success(request, f"Mensagem '{message_obj.title}' atualizada com sucesso.")
        return redirect('message:dashboard_message_list')

    # GET
    return render(request, 'dashboard/messages/form.html', {
        'users': recipients['users'],
        'grades': recipients['grades'],
        'classes': recipients['classes'],
        'message_types': message_types,
        'form_title': "Editar Mensagem",
        'current_title': message_obj.title,
        'current_content': message_obj.context,
        'current_type': message_obj.type_id,
        'current_users': message_obj.users.values_list('id', flat=True),
        'current_classes': message_obj.classes.values_list('id', flat=True),
        'current_grades': message_obj.grades.values_list('id', flat=True),
        'message': message_obj
    })


@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_message_delete(request, message_id):
    """
    ❌ Exclusão de Mensagem
      - notifica todos os destinatários
    """
    message_obj = get_object_or_404(Message, id=message_id)

    # Verifica permissão (apenas o criador ou administradores podem excluir)
    if message_obj.created_by != request.user and not request.user.roles.filter(
            role__name__in=["Diretor", "Coordenador"]).exists():
        messages.error(request, "Você não tem permissão para excluir esta mensagem.")
        return redirect('message:dashboard_message_list')

    message_title = message_obj.title

    # Coleta todos os destinatários antes da exclusão
    notified_users = set()

    # Usuários diretamente selecionados
    for user in message_obj.users.all():
        notified_users.add(user.id)

    # Alunos das turmas
    for turma in message_obj.classes.all():
        for student in Student.objects.filter(classes_assigned=turma):  # CORRIGIDO: current_class → classes_assigned
            if student.user:
                notified_users.add(student.user.id)
        for teacher in turma.teachers.all():
            notified_users.add(teacher.id)

    # Usuários das séries
    for grade in message_obj.grades.all():
        for role_type in ['coordinators', 'directors', 'colaborator']:
            if hasattr(grade, role_type):
                for user in getattr(grade, role_type).all():
                    notified_users.add(user.id)

        # Alunos e professores das turmas da série
        for turma in Class.objects.filter(grade=grade):
            for student in Student.objects.filter(classes_assigned=turma):  # CORRIGIDO: current_class → classes_assigned
                if student.user:
                    notified_users.add(student.user.id)
            for teacher in turma.teachers.all():
                notified_users.add(teacher.id)

    if request.method == "POST":
        # Exclui a mensagem
        message_obj.delete()

        # Notifica o usuário que excluiu
        if request.user.id in notified_users:
            notified_users.remove(request.user.id)

        # Responde com JSON para requisições AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Mensagem '{message_title}' excluída com sucesso."
            })

        # Responde com redirecionamento para requisições normais
        messages.success(request, f"Mensagem '{message_title}' excluída com sucesso.")
        return redirect('message:dashboard_message_list')

    # Se não for POST, retorna erro para AJAX ou redireciona para requisições normais
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Método não permitido. Use POST para excluir.'
        }, status=405)

    return redirect('message:dashboard_message_list')

@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_message_detail(request, message_id):
    """
    Visualização detalhada de uma mensagem no dashboard
    - marca como lida para o usuário atual
    """
    message_obj = get_object_or_404(Message, id=message_id)

    # Verifica se o usuário tem permissão para ver esta mensagem
    has_permission = False

    # Criador da mensagem
    if message_obj.created_by == request.user:
        has_permission = True

    # Destinatário direto
    elif message_obj.users.filter(id=request.user.id).exists():
        has_permission = True

    # Professor de uma turma destinatária
    elif message_obj.classes.filter(teachers=request.user).exists():
        has_permission = True

    # Aluno de uma turma destinatária
    elif Student.objects.filter(user=request.user, classes_assigned__in=message_obj.classes.all()).exists():  # CORRIGIDO: current_class → classes_assigned
        has_permission = True

    # Coordenador/Diretor/Colaborador de uma série destinatária
    elif message_obj.grades.filter(
        Q(coordinators=request.user) |
        Q(directors=request.user) |
        Q(colaborator=request.user)
    ).exists():
        has_permission = True

    # Aluno de uma turma de uma série destinatária
    elif Student.objects.filter(
        user=request.user,
        classes_assigned__grade__in=message_obj.grades.all()  # CORRIGIDO: current_class → classes_assigned
    ).exists():
        has_permission = True

    # Administrador
    elif request.user.roles.filter(role__name__in=["Diretor", "Coordenador"]).exists():
        has_permission = True

    if not has_permission:
        messages.error(request, "Você não tem permissão para visualizar esta mensagem.")
        return redirect('message:dashboard_message_list')

    # Marca como lida para o usuário atual
    received, created = ReceivedMessage.objects.get_or_create(
        message=message_obj,
        recipient=request.user,
        defaults={'read': True}
    )

    if not created and not received.read:
        received.read = True
        received.read_at = timezone.now()
        received.save()

    return render(request, 'dashboard/messages/detail.html', {
        'message': message_obj
    })

@login_required
def dashboard_mark_message_read(request, message_id):
    """
    Marca uma mensagem como lida via AJAX (dashboard)
    """
    if request.method == "POST":
        message_obj = get_object_or_404(Message, id=message_id)

        received, created = ReceivedMessage.objects.get_or_create(
            message=message_obj,
            recipient=request.user,
            defaults={'read': True}
        )

        if not created and not received.read:
            received.read = True
            received.read_at = timezone.now()
            received.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=405)

# =============================================================================
# VIEWS DO PARENT (FRONT-END PARA PAIS/RESPONSÁVEIS)
# =============================================================================

@login_required
def parent_messages_timeline(request):
    """
    Timeline de mensagens para pais/responsáveis com filtro de filhos
    """
    user = request.user

    # Buscar filhos do usuário
    filhos = get_user_children(user)

    # Filtro por filho específico
    filho_id = request.GET.get('filho')
    filho_selecionado = None  # Inicializa como None
    visible_messages = Message.objects.none()  # Inicializa como um queryset vazio

    if filho_id and filho_id.isdigit():
        try:
            filho_selecionado = Student.objects.get(id=int(filho_id), parents__user=user)  # Garante que o filho pertence ao pai

            # Buscar as turmas e séries do filho
            turmas = filho_selecionado.classes_assigned.all()
            series = [turma.grade for turma in turmas]

            # Filtrar as mensagens com base nas turmas e séries do filho
            visible_messages = Message.objects.filter(
                Q(users=filho_selecionado.user) |  # Mensagens enviadas diretamente para o usuário do filho
                Q(classes__in=turmas) |  # Mensagens enviadas para as turmas do filho
                Q(grades__in=series)  # Mensagens enviadas para as séries do filho
            ).distinct()

        except Student.DoesNotExist:
            # Se o filho não existe ou não pertence ao usuário, exibir mensagens para todos os filhos
            visible_messages = get_visible_messages(user)
    else:
        # Sem filtro específico, exibir mensagens para todos os filhos
        visible_messages = get_visible_messages(user)

    # Aplicar filtros adicionais (tipo e busca)
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
        'filhos': filhos,
        'filho_selecionado': filho_selecionado,  # Passa o objeto filho_selecionado para o template
    })



@login_required
def parent_message_detail(request, id):
    """
    Visualização detalhada de uma mensagem para pais/responsáveis
    """
    queryset = get_visible_messages(request.user)
    message = get_object_or_404(queryset, id=id)

    # Marca como lida
    MessageReadLog.objects.get_or_create(
        message=message,
        user=request.user,
        defaults={'read_at': timezone.now()}
    )

    return render(request, 'message/message_detail.html', {'message': message})

@login_required
def parent_event_json(request):
    """
    Retorna eventos em formato JSON para o calendário
    """
    user = request.user
    context = get_user_visibility_context(user)  # Centraliza as permissões/visibilidade

    # Filtra eventos pelas turmas do usuário
    eventos = Event.objects.filter(classes__in=context["user_classes"]).distinct()

    # Monta a lista de eventos para o calendário
    data = []
    for evento in eventos:
        data.append({
            "id": evento.id,
            "title": evento.titulo,
            "start": evento.inicio.isoformat(),
            "end": evento.fim.isoformat() if evento.fim else None,
            # "description": evento.descricao,  # REMOVIDO: não existe
            # "allDay": getattr(evento, "dia_todo", False),  # REMOVIDO: não existe
            # "className": f"event-type-{getattr(evento, 'tipo', '')}",  # REMOVIDO: não existe
            # "url": reverse('message:parent_event_detail', kwargs={'id': evento.id})  # Só inclua se existir essa view/URL
        })

    return JsonResponse(data, safe=False)


@login_required
@role_required(["Diretor", "Coordenador"])
def dashboard_event_create(request):
    """
    ✅ Criação de Evento via Dashboard
    """
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            form.save_m2m()  # Salva as relações ManyToMany (como classes)

            messages.success(request, f"Evento '{event.titulo}' criado com sucesso.")
            return redirect('message:dashboard_event_list')  # Redireciona para a lista de eventos
        else:
            messages.error(request, "Erro ao criar o evento. Verifique os campos.")
    else:
        form = EventForm()  # Cria um formulário vazio

    return render(request, 'dashboard/events/form.html', {
        'form': form,
        'form_title': "Novo Evento",
        'form_subtitle': "Preencha os campos para criar um novo evento."
    })


@role_required(["Diretor", "Coordenador"])
def dashboard_event_list(request):
    titulo = request.GET.get('titulo', '').strip()
    class_id = request.GET.get('class_id', '')
    inicio = request.GET.get('inicio', '')

    events_qs = Event.objects.prefetch_related('classes').order_by('-inicio')

    if titulo:
        events_qs = events_qs.filter(titulo__icontains=titulo)
    if class_id:
        events_qs = events_qs.filter(classes__id=class_id)
    if inicio:
        events_qs = events_qs.filter(inicio__date=inicio)

    paginator = Paginator(events_qs.distinct(), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    classes = Class.objects.all().order_by('name')

    return render(request, 'dashboard/events/list.html', {
        'events': page_obj.object_list,
        'page_obj': page_obj,
        'classes': classes,
        'current_titulo': titulo,
        'current_class_id': class_id,
        'current_inicio': inicio,
        'form_title': 'Eventos Cadastrados',
    })


@login_required
@role_required(["Diretor", "Coordenador"])
def dashboard_event_edit(request, event_id):
    """
    ✏️ Edição de Evento via Dashboard
    """
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f"Evento '{event.titulo}' atualizado com sucesso.")
            return redirect('message:dashboard_event_list')
        else:
            messages.error(request, "Erro ao atualizar o evento. Verifique os campos.")
    else:
        form = EventForm(instance=event)
    return render(request, 'dashboard/events/form.html', {
        'form': form,
        'form_title': "Editar Evento",
        'form_subtitle': f"Edite as informações do evento \"{event.titulo}\"."
    })

@login_required
@role_required(["Diretor", "Coordenador"])
def dashboard_event_delete(request, event_id):
    """
    🗑️ Exclusão de Evento via Dashboard
    """
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        titulo = event.titulo
        event.delete()
        messages.success(request, f"Evento '{titulo}' excluído com sucesso.")
        return redirect('message:dashboard_event_list')
    else:
        messages.error(request, "A exclusão deve ser feita via POST.")
        return redirect('message:dashboard_event_list')

@login_required
def parent_calendar_view(request):
    """
    Visualização do calendário para pais/responsáveis
    """
    return render(request, 'message/calendar.html')