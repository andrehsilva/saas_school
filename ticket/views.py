from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as msg
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from school.models import Grade, Class, Subject, Student, Parent

from .models import Ticket, TicketMessage, TicketAllowedResponder, TicketCategory
from school.models import Parent
from notification.utils import send_notification
from dashboard.permissions import role_required

from django.contrib.auth import get_user_model
User = get_user_model()


def generate_ticket_number():
    return get_random_string(8).upper()


@login_required
def ticket_list(request):
    user = request.user
    search_query = request.GET.get('q', '').strip().lower()

    status_map = {
        'aberto': 'open',
        'fechado': 'closed',
        'em andamento': 'in_progress',
        'andamento': 'in_progress',
    }

    try:
        parent = Parent.objects.get(user=user)
        tickets = Ticket.objects.filter(parent=parent)
    except Parent.DoesNotExist:
        if TicketAllowedResponder.objects.filter(user=user).exists():
            tickets = Ticket.objects.all()
        else:
            tickets = Ticket.objects.none()

    if search_query:
        status_value = status_map.get(search_query)
        if status_value:
            tickets = tickets.filter(status=status_value)
        else:
            tickets = tickets.filter(
                Q(subject__icontains=search_query) |
                Q(ticket_number__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(created_at__icontains=search_query)
            )

    tickets = tickets.order_by('-created_at')
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'ticket/ticket_list.html', {
        'tickets': page_obj,
        'page_obj': page_obj,
        'search_query': request.GET.get('q', ''),
    })


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    user = request.user
    is_parent = hasattr(user, 'parent')
    is_responder = TicketAllowedResponder.objects.filter(user=user).exists()

    if is_parent and ticket.parent.user != user and not is_responder:
        return redirect('ticket:ticket_list')

    if request.method == 'POST':
        if 'status' in request.POST and is_responder:
            new_status = request.POST.get('status')
            if new_status in dict(Ticket.STATUS_CHOICES):
                ticket.status = new_status
                ticket.save()
                msg.success(request, "Status do ticket atualizado com sucesso!")
                return redirect('ticket:ticket_detail', ticket_id=ticket.id)

        if ticket.status != 'closed':
            message_text = request.POST.get('message')
            attachment = request.FILES.get('attachment')

            if message_text:
                TicketMessage.objects.create(
                    ticket=ticket,
                    sender=user,
                    message=message_text,
                    attachment=attachment
                )

                if ticket.status == 'open':
                    ticket.status = 'in_progress'
                    ticket.save()

                try:
                    ticket_url = request.build_absolute_uri(reverse('ticket:ticket_detail', args=[ticket.id]))
                except:
                    ticket_url = f"/ticket/{ticket.id}/"

                notified_users = set()

                # Pai respondeu → notifica escola
                if ticket.parent.user == user:
                    responders = TicketAllowedResponder.objects.filter(
                        categories=ticket.category
                    ).select_related('user')
                    for responder in responders:
                        recipient = responder.user
                        if recipient and recipient.id not in notified_users:
                            send_notification(
                                recipients=recipient,
                                title=f"Novo comentário no ticket: {ticket.subject}",
                                message=message_text,
                                url=ticket_url
                            )
                            notified_users.add(recipient.id)

                # Escola respondeu → notifica pai
                else:
                    parent_user = ticket.parent.user
                    if parent_user and parent_user.id not in notified_users:
                        send_notification(
                            recipients=parent_user,
                            title=f"Resposta ao seu ticket: {ticket.subject}",
                            message=message_text,
                            url=ticket_url
                        )

                msg.success(request, "Mensagem enviada com sucesso!")
                return redirect('ticket:ticket_detail', ticket_id=ticket.id)

    ticket_messages = ticket.messages.all().order_by('created_at')

    return render(request, 'ticket/ticket_detail.html', {
        'ticket': ticket,
        'ticket_messages': ticket_messages,
        'is_responder': is_responder,
    })


@login_required
def create_ticket(request):
    user = request.user
    try:
        parent = Parent.objects.get(user=user)
    except Parent.DoesNotExist:
        msg.error(request, "Apenas responsáveis podem criar tickets.")
        return redirect('ticket:ticket_list')

    categories = TicketCategory.objects.all()

    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        category_id = request.POST.get('category')
        attachment = request.FILES.get('attachment')

        if subject and message:
            category = TicketCategory.objects.filter(id=category_id).first()

            ticket = Ticket.objects.create(
                parent=parent,
                subject=subject,
                category=category,
                ticket_number=generate_ticket_number()
            )

            TicketMessage.objects.create(
                ticket=ticket,
                sender=user,
                message=message,
                attachment=attachment
            )

            try:
                ticket_url = request.build_absolute_uri(reverse('ticket:ticket_detail', args=[ticket.id]))
            except:
                ticket_url = f"/ticket/{ticket.id}/"

            responders = TicketAllowedResponder.objects.filter(categories=category).select_related('user')
            notified_users = set()

            for responder in responders:
                recipient = responder.user
                if recipient and recipient.id not in notified_users:
                    send_notification(
                        recipients=recipient,
                        title=f"Novo ticket aberto: {subject}",
                        message=message,
                        url=ticket_url
                    )
                    notified_users.add(recipient.id)

            msg.success(request, "Ticket criado com sucesso!")
            return redirect('ticket:ticket_list')

        msg.error(request, "Assunto e mensagem são obrigatórios.")

    return render(request, 'ticket/create_ticket.html', {'categories': categories})


@login_required
def close_ticket(request, ticket_id):
    user = request.user
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if not TicketAllowedResponder.objects.filter(user=user).exists():
        msg.error(request, "Você não tem permissão para fechar este ticket.")
        return redirect('ticket:ticket_detail', ticket_id=ticket.id)

    ticket.status = 'closed'
    ticket.save()

    try:
        ticket_url = request.build_absolute_uri(reverse('ticket:ticket_detail', args=[ticket.id]))
    except:
        ticket_url = f"/ticket/{ticket.id}/"

    if ticket.parent and ticket.parent.user:
        send_notification(
            recipients=ticket.parent.user,
            title="Ticket fechado",
            message=f"Seu ticket '{ticket.subject}' foi encerrado.",
            url=ticket_url
        )

    msg.success(request, "Ticket fechado com sucesso.")
    return redirect('ticket:ticket_detail', ticket_id=ticket.id)





#####dashboard#######


@login_required
@role_required(["Diretor", "Coordenador", "Colaborador", "Professor"])
def dashboard_ticket_list(request):
    """
    
    Lista os tickets do dashboard, mas respeita a regra de permissão para resposta.
    Apenas usuários autorizados a responder podem visualizar os tickets.
    """
    user = request.user

    # Verifica se o usuário tem permissão para visualizar/responder tickets
    if not TicketAllowedResponder.objects.filter(user=user).exists():
        msg.error(request, "Você não tem permissão para visualizar os tickets.")
        return redirect('dashboard:home')  # ou para qualquer outra view segura
    
    

    # Filtros da query string
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')

    status_map = {
        'aberto': 'open',
        'fechado': 'closed',
        'em andamento': 'in_progress',
        'andamento': 'in_progress',
    }

    # Apenas tickets das categorias em que o usuário pode responder
    allowed_categories = TicketAllowedResponder.objects.filter(user=user).values_list('categories', flat=True)
    tickets = Ticket.objects.filter(category_id__in=allowed_categories).select_related('parent__user', 'category')

    # Filtros
    if search_query:
        status_value = status_map.get(search_query.lower())
        if status_value:
            tickets = tickets.filter(status=status_value)
        else:
            tickets = tickets.filter(
                Q(subject__icontains=search_query) |
                Q(ticket_number__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(parent__user__first_name__icontains=search_query) |
                Q(parent__user__last_name__icontains=search_query)
            )

    if status_filter:
        tickets = tickets.filter(status=status_filter)

    if category_filter:
        tickets = tickets.filter(category_id=category_filter)

    tickets = tickets.order_by('-created_at')
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = TicketCategory.objects.filter(id__in=allowed_categories)
    status_choices = Ticket.STATUS_CHOICES

    return render(request, 'dashboard/tickets/list.html', {
        'tickets': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'status_choices': status_choices,
        'search_query': search_query,
        'current_status': status_filter,
        'current_category': category_filter,
    })



@login_required
@role_required(["Diretor", "Coordenador", "Colaborador", "Professor"])
def dashboard_ticket_detail(request, ticket_id):
    """
    Visualização detalhada de um ticket no dashboard
    Permite responder e fechar o ticket
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    user = request.user

    if request.method == 'POST':
        # Fechar ticket
        if 'close_ticket' in request.POST:
            if ticket.status != 'closed':
                ticket.status = 'closed'
                ticket.save()

                # Notifica o pai
                try:
                    ticket_url = request.build_absolute_uri(
                        reverse('ticket:dashboard_ticket_detail', args=[ticket.id])
                    )
                except:
                    ticket_url = f"/dashboard/tickets/{ticket.id}/"

                if ticket.parent and ticket.parent.user:
                    send_notification(
                        recipients=ticket.parent.user,
                        title="Ticket fechado",
                        message=f"Seu ticket '{ticket.subject}' foi encerrado pela escola.",
                        url=ticket_url
                    )

                msg.success(request, "Ticket fechado com sucesso!")
                return redirect('ticket:dashboard_ticket_detail', ticket_id=ticket.id)

        # Responder ticket
        elif 'reply_ticket' in request.POST:
            if ticket.status != 'closed':
                message_text = request.POST.get('message', '').strip()
                attachment = request.FILES.get('attachment')

                if message_text:
                    # Cria a mensagem
                    TicketMessage.objects.create(
                        ticket=ticket,
                        sender=user,
                        message=message_text,
                        attachment=attachment
                    )

                    # Atualiza status se necessário
                    if ticket.status == 'open':
                        ticket.status = 'in_progress'
                        ticket.save()

                    # Notifica o pai
                    try:
                        ticket_url = request.build_absolute_uri(
                            reverse('ticket:dashboard_ticket_detail', args=[ticket.id])
                        )
                    except:
                        ticket_url = f"/dashboard/tickets/{ticket.id}/"

                    if ticket.parent and ticket.parent.user:
                        send_notification(
                            recipients=ticket.parent.user,
                            title=f"Resposta ao seu ticket: {ticket.subject}",
                            message=message_text,
                            url=ticket_url
                        )

                    msg.success(request, "Resposta enviada com sucesso!")
                    return redirect('ticket:dashboard_ticket_detail', ticket_id=ticket.id)
                else:
                    msg.error(request, "A mensagem não pode estar vazia.")

    # Busca todas as mensagens do ticket
    ticket_messages = ticket.messages.all().order_by('created_at')

    return render(request, 'dashboard/tickets/detail.html', {
        'ticket': ticket,
        'ticket_messages': ticket_messages,
    })


@login_required
@role_required(["Diretor", "Coordenador", "Colaborador", "Professor"])
def dashboard_ticket_close(request, ticket_id):
    """
    Fecha um ticket via AJAX (para modal de confirmação)
    """
    if request.method == "POST":
        ticket = get_object_or_404(Ticket, id=ticket_id)

        if ticket.status != 'closed':
            ticket.status = 'closed'
            ticket.save()

            # Notifica o pai
            try:
                ticket_url = request.build_absolute_uri(
                    reverse('ticket:dashboard_ticket_detail', args=[ticket.id])
                )
            except:
                ticket_url = f"/dashboard/tickets/{ticket.id}/"

            if ticket.parent and ticket.parent.user:
                send_notification(
                    recipients=ticket.parent.user,
                    title="Ticket fechado",
                    message=f"Seu ticket '{ticket.subject}' foi encerrado pela escola.",
                    url=ticket_url
                )

            # Responde com JSON para requisições AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"Ticket #{ticket.ticket_number} fechado com sucesso."
                })

            msg.success(request, f"Ticket #{ticket.ticket_number} fechado com sucesso.")
            return redirect('ticket:dashboard_ticket_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Este ticket já está fechado.'
                })
            msg.warning(request, "Este ticket já está fechado.")
            return redirect('ticket:dashboard_ticket_detail', ticket_id=ticket.id)

    # Se não for POST, retorna erro para AJAX ou redireciona
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Método não permitido. Use POST para fechar.'
        }, status=405)

    return redirect('ticket:dashboard_ticket_list')


@login_required
@role_required(["Diretor", "Coordenador", "Colaborador", "Professor"])
def dashboard_ticket_reopen(request, ticket_id):
    """
    Reabre um ticket via AJAX (para modal de confirmação)
    """
    if request.method == "POST":
        ticket = get_object_or_404(Ticket, id=ticket_id)

        if ticket.status == 'closed':
            ticket.status = 'open'  # ou 'in_progress' se preferir
            ticket.save()

            # Notifica o responsável
            try:
                ticket_url = request.build_absolute_uri(
                    reverse('ticket:dashboard_ticket_detail', args=[ticket.id])
                )
            except:
                ticket_url = f"/dashboard/tickets/{ticket.id}/"

            if ticket.parent and ticket.parent.user:
                send_notification(
                    recipients=ticket.parent.user,
                    title="Ticket reaberto",
                    message=f"Seu ticket '{ticket.subject}' foi reaberto pela escola.",
                    url=ticket_url
                )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"Ticket #{ticket.ticket_number} reaberto com sucesso."
                })

            msg.success(request, f"Ticket #{ticket.ticket_number} reaberto com sucesso.")
            return redirect('ticket:dashboard_ticket_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Este ticket não está fechado.'
                })
            msg.warning(request, "Este ticket não está fechado.")
            return redirect('ticket:dashboard_ticket_detail', ticket_id=ticket.id)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Método não permitido. Use POST para reabrir.'
        }, status=405)

    return redirect('ticket:dashboard_ticket_list')



##permissão de ticket#######
############################

@login_required
@role_required(["Diretor"])
def allowed_responders_list(request):
    responders = TicketAllowedResponder.objects.select_related('user').prefetch_related('categories').all()
    return render(request, 'dashboard/tickets/allowed_responders_list.html', {
        'responders': responders,
    })


@login_required
@role_required(["Diretor"])
def allowed_responder_create(request):
    # Exclui alunos e pais da lista de usuários
    student_user_ids = Student.objects.values_list('user_id', flat=True)
    parent_user_ids = Parent.objects.values_list('user_id', flat=True)
    users = User.objects.exclude(id__in=student_user_ids).exclude(id__in=parent_user_ids).order_by('first_name', 'last_name')
    categories = TicketCategory.objects.all()

    if request.method == 'POST':
        user_id = request.POST.get('user')
        category_ids = request.POST.getlist('categories')
        if not user_id or not category_ids:
            msg.error(request, "Selecione um usuário e pelo menos uma categoria.")
            return render(request, 'dashboard/tickets/allowed_responder_form.html', {
                'users': users,
                'categories': categories,
            })
        user = get_object_or_404(User, id=user_id)
        responder, created = TicketAllowedResponder.objects.get_or_create(user=user)
        responder.categories.set(category_ids)
        responder.save()
        msg.success(request, "Permissão criada/atualizada com sucesso!")
        return redirect('ticket:allowed_responders_list')

    return render(request, 'dashboard/tickets/allowed_responder_form.html', {
        'users': users,
        'categories': categories,
    })


@login_required
@role_required(["Diretor"])
def allowed_responder_edit(request, pk):
    responder = get_object_or_404(TicketAllowedResponder, pk=pk)
    users = User.objects.all()
    categories = TicketCategory.objects.all()

    if request.method == 'POST':
        user_id = request.POST.get('user')
        category_ids = request.POST.getlist('categories')
        responder.user = User.objects.get(id=user_id)
        responder.categories.set(category_ids)
        responder.save()
        msg.success(request, "Permissão atualizada com sucesso!")
        return redirect('ticket:allowed_responders_list')

    return render(request, 'dashboard/tickets/allowed_responder_form.html', {
        'responder': responder,
        'users': users,
        'categories': categories,
    })


@login_required
@role_required(["Diretor"])
def allowed_responder_delete(request, pk):
    responder = get_object_or_404(TicketAllowedResponder, pk=pk)

    if request.method == 'POST':
        responder.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        msg.success(request, "Permissão removida com sucesso!")
        return redirect('ticket:allowed_responders_list')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)

    return redirect('ticket:allowed_responders_list')

