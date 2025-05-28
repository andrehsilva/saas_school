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

# =============================================================================
# VIEWS DO DASHBOARD (ADMIN/GESTÃO)
# =============================================================================

@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_message_list(request):
    """
    Lista todas as mensagens que o usuário tem permissão para ver
    """
    # Usuários com papéis administrativos podem ver todas as mensagens
    is_admin = request.user.roles.filter(role__name__in=["Diretor", "Coordenador", "Colaborador"]).exists()

    if is_admin:
        all_messages = Message.objects.all().order_by('-created_at')
    else:
        # Professores veem apenas mensagens que criaram ou que foram enviadas para eles
        all_messages = Message.objects.filter(
            Q(created_by=request.user) |
            Q(users=request.user) |
            Q(classes__teachers=request.user) |
            Q(grades__in=Grade.objects.filter(
                Q(coordinators=request.user) |
                Q(directors=request.user) |
                Q(colaborator=request.user)
            ))
        ).distinct().order_by('-created_at')

    # Preparar mensagens com permissões para o template
    messages_with_permissions = []
    for msg in all_messages:
        # Usuário pode editar se for admin ou criador da mensagem
        can_edit = is_admin or msg.created_by == request.user
        messages_with_permissions.append({
            'message': msg,
            'can_edit': can_edit
        })

    return render(request, 'dashboard/messages/list.html', {
        'messages_with_permissions': messages_with_permissions,
        'current_title': '',
        'current_content': '',
        'current_type': '',
        'current_users': [],
        'current_classes': [],
        'current_grades': []
    })

@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_message_create(request):
    """
    ✅ Criação de Mensagem
      - notifica todos os destinatários (usuários, turmas, séries)
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

        # Cria a mensagem
        new_message = Message.objects.create(
            title=title,
            context=content,
            created_by=request.user,
            type_id=type_id if type_id else None
        )

        # Adiciona os destinatários
        if user_ids:
            new_message.users.set(User.objects.filter(id__in=user_ids))
        if class_ids:
            new_message.classes.set(Class.objects.filter(id__in=class_ids))
        if grade_ids:
            new_message.grades.set(Grade.objects.filter(id__in=grade_ids))

        # --- NOTIFICAÇÕES ---
        message_url = request.build_absolute_uri(_get_message_url(new_message))
        notified_users = set()

        # 1. Notificar o criador da mensagem
        if request.user.id not in notified_users:
            send_notification(
                recipients=request.user,
                title="Mensagem Enviada",
                message=f"Sua mensagem '{new_message.title}' foi enviada com sucesso.",
                url=message_url
            )
            notified_users.add(request.user.id)

        # 2. Notificar usuários diretamente selecionados
        for user in new_message.users.all():
            if user.id not in notified_users:
                send_notification(
                    recipients=user,
                    title=new_message.title,
                    message=new_message.context[:100] + "..." if len(new_message.context) > 100 else new_message.context,
                    url=message_url
                )
                notified_users.add(user.id)

        # 3. Notificar turmas
        for turma in new_message.classes.all():
            # Cria ReceivedMessage para cada aluno da turma
            for student in Student.objects.filter(current_class=turma):
                if student.user and student.user.id not in notified_users:
                    ReceivedMessage.objects.create(
                        message=new_message,
                        user=student.user,
                        is_read=False
                    )
                    send_notification(
                        recipients=student.user,
                        title=new_message.title,
                        message=new_message.context[:100] + "..." if len(new_message.context) > 100 else new_message.context,
                        url=message_url
                    )
                    notified_users.add(student.user.id)

            # Notifica professores da turma
            for teacher in turma.teachers.all():
                if teacher.id not in notified_users:
                    send_notification(
                        recipients=teacher,
                        title=f"Nova mensagem para turma {turma.name}",
                        message=f"'{new_message.title}' - {new_message.context[:50]}...",
                        url=message_url
                    )
                    notified_users.add(teacher.id)

        # 4. Notificar séries (todas as turmas da série)
        for grade in new_message.grades.all():
            # Notifica coordenadores e diretores da série
            for role_type in ['coordinators', 'directors', 'colaborator']:
                if hasattr(grade, role_type):
                    for user in getattr(grade, role_type).all():
                        if user.id not in notified_users:
                            send_notification(
                                recipients=user,
                                title=f"Nova mensagem para série {grade.name}",
                                message=f"'{new_message.title}' - {new_message.context[:50]}...",
                                url=message_url
                            )
                            notified_users.add(user.id)

            # Notifica todas as turmas da série
            for turma in Class.objects.filter(grade=grade):
                # Alunos
                for student in Student.objects.filter(current_class=turma):
                    if student.user and student.user.id not in notified_users:
                        ReceivedMessage.objects.create(
                            message=new_message,
                            user=student.user,
                            is_read=False
                        )
                        send_notification(
                            recipients=student.user,
                            title=new_message.title,
                            message=new_message.context[:100] + "..." if len(new_message.context) > 100 else new_message.context,
                            url=message_url
                        )
                        notified_users.add(student.user.id)

                # Professores
                for teacher in turma.teachers.all():
                    if teacher.id not in notified_users:
                        send_notification(
                            recipients=teacher,
                            title=f"Nova mensagem para série {grade.name}",
                            message=f"'{new_message.title}' - {new_message.context[:50]}...",
                            url=message_url
                        )
                        notified_users.add(teacher.id)

        messages.success(request, f"Mensagem '{new_message.title}' enviada com sucesso.")
        return redirect('message:dashboard_message_list')

    # GET
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
        'current_grades': [],
        'message': None
    })

@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_message_edit(request, message_id):
    """
    🔄 Edição de Mensagem
      - notifica todos os destinatários atuais
      - notifica destinatários adicionados ➕
      - notifica destinatários removidos ➖
    """
    message_obj = get_object_or_404(Message, id=message_id)

    # Verifica permissão (apenas o criador ou administradores podem editar)
    if message_obj.created_by != request.user and not request.user.roles.filter(
            role__name__in=["Diretor", "Coordenador"]).exists():
        messages.error(request, "Você não tem permissão para editar esta mensagem.")
        return redirect('message:dashboard_message_list')

    recipients = get_eligible_recipients()
    message_types = get_message_types()

    # Captura os destinatários atuais antes da edição
    old_users = set(message_obj.users.all().values_list('id', flat=True))
    old_classes = set(message_obj.classes.all().values_list('id', flat=True))
    old_grades = set(message_obj.grades.all().values_list('id', flat=True))
    old_title = message_obj.title
    old_content = message_obj.context

    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        type_id = request.POST.get('type')
        user_ids = [int(i) for i in request.POST.getlist('users') if i.isdigit()]
        class_ids = [int(i) for i in request.POST.getlist('classes') if i.isdigit()]
        grade_ids = [int(i) for i in request.POST.getlist('grades') if i.isdigit()]

        if not title or not content:
            messages.error(request, "Título e conteúdo são obrigatórios.")
            return render(request, 'dashboard/messages/form.html', {
                'message': message_obj,
                'users': recipients['users'],
                'grades': recipients['grades'],
                'classes': recipients['classes'],
                'message_types': message_types,
                'current_title': title,
                'current_content': content,
                'current_type': type_id,
                'current_users': [str(u) for u in user_ids],
                'current_classes': [str(c) for c in class_ids],
                'current_grades': [str(g) for g in grade_ids],
                'form_title': f"Editar Mensagem: {message_obj.title}"
            })

        # Atualiza a mensagem
        message_obj.title = title
        message_obj.context = content
        message_obj.type_id = type_id if type_id else None
        message_obj.save()

        # Atualiza os destinatários
        message_obj.users.set(User.objects.filter(id__in=user_ids))
        message_obj.classes.set(Class.objects.filter(id__in=class_ids))
        message_obj.grades.set(Grade.objects.filter(id__in=grade_ids))

        # --- NOTIFICAÇÕES ---
        message_url = request.build_absolute_uri(_get_message_url(message_obj))
        notified_users = set()

        # 1. Notificar o editor da mensagem
        if request.user.id not in notified_users:
            send_notification(
                recipients=request.user,
                title="Mensagem Atualizada",
                message=f"A mensagem '{message_obj.title}' foi atualizada com sucesso.",
                url=message_url
            )
            notified_users.add(request.user.id)

        # 2. Notificar o criador original (se for diferente do editor)
        if message_obj.created_by and message_obj.created_by.id != request.user.id and message_obj.created_by.id not in notified_users:
            send_notification(
                recipients=message_obj.created_by,
                title="Sua mensagem foi editada",
                message=f"A mensagem '{old_title}' foi editada por {request.user.get_full_name() or request.user.username}.",
                url=message_url
            )
            notified_users.add(message_obj.created_by.id)

        # 3. Verificar mudanças nos destinatários
        current_users = set(user_ids)
        current_classes = set(class_ids)
        current_grades = set(grade_ids)

        # Usuários adicionados
        added_users = current_users - old_users
        for user_id in added_users:
            try:
                user = User.objects.get(id=user_id)
                if user.id not in notified_users:
                    send_notification(
                        recipients=user,
                        title=message_obj.title,
                        message=message_obj.context[:100] + "..." if len(message_obj.context) > 100 else message_obj.context,
                        url=message_url
                    )
                    notified_users.add(user.id)

                    # Cria ReceivedMessage para o novo usuário
                    ReceivedMessage.objects.create(
                        message=message_obj,
                        user=user,
                        is_read=False
                    )
            except User.DoesNotExist:
                continue

        # Usuários removidos
        removed_users = old_users - current_users
        for user_id in removed_users:
            try:
                user = User.objects.get(id=user_id)
                if user.id not in notified_users:
                    send_notification(
                        recipients=user,
                        title="Removido de mensagem",
                        message=f"Você foi removido como destinatário da mensagem '{message_obj.title}'.",
                        url="#"
                    )
                    notified_users.add(user.id)

                    # Remove ReceivedMessage para o usuário removido
                    ReceivedMessage.objects.filter(message=message_obj, user=user).delete()
            except User.DoesNotExist:
                continue

        # 4. Notificar sobre alterações no conteúdo para destinatários atuais
        if old_title != title or old_content != content:
            # Todos os usuários diretamente selecionados
            for user in message_obj.users.all():
                if user.id not in notified_users:
                    send_notification(
                        recipients=user,
                        title="Mensagem atualizada",
                        message=f"A mensagem '{message_obj.title}' foi atualizada.",
                        url=message_url
                    )
                    notified_users.add(user.id)

            # Todas as turmas atuais
            for turma in message_obj.classes.all():
                # Alunos
                for student in Student.objects.filter(current_class=turma):
                    if student.user and student.user.id not in notified_users:
                        send_notification(
                            recipients=student.user,
                            title="Mensagem atualizada",
                            message=f"A mensagem '{message_obj.title}' foi atualizada.",
                            url=message_url
                        )
                        notified_users.add(student.user.id)

                # Professores
                for teacher in turma.teachers.all():
                    if teacher.id not in notified_users:
                        send_notification(
                            recipients=teacher,
                            title="Mensagem atualizada",
                            message=f"A mensagem '{message_obj.title}' para a turma {turma.name} foi atualizada.",
                            url=message_url
                        )
                        notified_users.add(teacher.id)

            # Todas as séries atuais
            for grade in message_obj.grades.all():
                # Coordenadores e diretores
                for role_type in ['coordinators', 'directors', 'colaborator']:
                    if hasattr(grade, role_type):
                        for user in getattr(grade, role_type).all():
                            if user.id not in notified_users:
                                send_notification(
                                    recipients=user,
                                    title="Mensagem atualizada",
                                    message=f"A mensagem '{message_obj.title}' para a série {grade.name} foi atualizada.",
                                    url=message_url
                                )
                                notified_users.add(user.id)

        messages.success(request, f"Mensagem '{message_obj.title}' atualizada com sucesso.")
        return redirect('message:dashboard_message_list')

    # GET
    return render(request, 'dashboard/messages/form.html', {
        'message': message_obj,
        'users': recipients['users'],
        'grades': recipients['grades'],
        'classes': recipients['classes'],
        'message_types': message_types,
        'current_title': message_obj.title,
        'current_content': message_obj.context,
        'current_type': message_obj.type_id if message_obj.type else None,
        'current_users': [str(u.id) for u in message_obj.users.all()],
        'current_classes': [str(c.id) for c in message_obj.classes.all()],
        'current_grades': [str(g.id) for g in message_obj.grades.all()],
        'form_title': f"Editar Mensagem: {message_obj.title}"
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
        for student in Student.objects.filter(current_class=turma):
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
            for student in Student.objects.filter(current_class=turma):
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

        send_notification(
            recipients=request.user,
            title="Mensagem Excluída",
            message=f"A mensagem '{message_title}' foi excluída com sucesso.",
            url=_get_message_list_url()
        )

        # Notifica todos os destinatários
        for user_id in notified_users:
            try:
                user = User.objects.get(id=user_id)
                send_notification(
                    recipients=user,
                    title="Mensagem Removida",
                    message=f"A mensagem '{message_title}' foi removida pelo administrador.",
                    url=_get_message_list_url()
                )
            except User.DoesNotExist:
                continue

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f"Mensagem '{message_title}' excluída com sucesso."})

        messages.success(request, f"Mensagem '{message_title}' excluída com sucesso.")

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
    elif Student.objects.filter(user=request.user, current_class__in=message_obj.classes.all()).exists():
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
        current_class__grade__in=message_obj.grades.all()
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
        user=request.user,
        defaults={'is_read': True}
    )

    if not created and not received.is_read:
        received.is_read = True
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
            user=request.user,
            defaults={'is_read': True}
        )

        if not created and not received.is_read:
            received.is_read = True
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
    Timeline de mensagens para pais/responsáveis
    """
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

@login_required
def parent_calendar_view(request):
    """
    Visualização do calendário para pais/responsáveis
    """
    return render(request, 'message/calendar.html')