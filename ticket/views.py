from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as msg
from django.db.models import Q
from .models import Ticket, TicketMessage, TicketAllowedResponder, TicketCategory
from school.models import Parent
from django.utils.crypto import get_random_string
from django.shortcuts import redirect
from .models import Ticket, TicketAllowedResponder
from django.core.paginator import Paginator

def generate_ticket_number():
    return get_random_string(8).upper()


@login_required
def ticket_list(request):
    user = request.user
    search_query = request.GET.get('q', '').strip().lower()

    # Mapeamento de status em português para valores do banco
    status_map = {
        'aberto': 'open',
        'fechado': 'closed',
        'em andamento': 'in_progress',
        'andamento': 'in_progress',  # opção alternativa
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
        # Substitui valor da busca se for um status em português
        status_value = status_map.get(search_query)
        if status_value:
            tickets = tickets.filter(status=status_value)
        else:
            tickets = tickets.filter(
            Q(subject__icontains=search_query) |
            Q(ticket_number__icontains=search_query) |
            Q(category__name__icontains=search_query) |  # <-- ADICIONADO
            Q(created_at__icontains=search_query)
        )

    tickets = tickets.order_by('-created_at')

    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'ticket/ticket_list.html', {
        'tickets': page_obj,
        'page_obj': page_obj,
        'search_query': request.GET.get('q', ''),  # mantém o valor original no input
    })

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    user = request.user

    # Verifica permissão
    is_parent = hasattr(user, 'parent')
    is_responder = TicketAllowedResponder.objects.filter(user=user).exists()
    allowed_responders = TicketAllowedResponder.objects.values_list('user', flat=True)

    if is_parent and ticket.parent.user != user and not is_responder:
        return redirect('ticket_list')

    if request.method == 'POST' and ticket.status != 'closed':
        message = request.POST.get('message')
        attachment = request.FILES.get('attachment')

        if message:
            TicketMessage.objects.create(
                ticket=ticket,
                sender=user,
                message=message,
                attachment=attachment
            )
            # Atualiza o status para "em_andamento" se estiver "aberto"
            if ticket.status == 'open':
                ticket.status = 'in_progress'
                ticket.save()

            msg.success(request, "Mensagem enviada com sucesso!")
            return redirect('ticket_detail', ticket_id=ticket.id)

    messages = ticket.messages.all().order_by('created_at')
    return render(request, 'ticket/ticket_detail.html', {
        'ticket': ticket,
        'messages': messages,
        'is_responder': is_responder,
        'allowed_responders': allowed_responders,
    })


@login_required
def create_ticket(request):
    user = request.user
    try:
        parent = Parent.objects.get(user=user)
    except Parent.DoesNotExist:
        msg.error(request, "Apenas responsáveis podem criar tickets.")
        return redirect('ticket_list')

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

            msg.success(request, "Ticket criado com sucesso!")
            return redirect('ticket_detail', ticket_id=ticket.id)

        else:
            msg.error(request, "Assunto e mensagem são obrigatórios.")

    return render(request, 'ticket/create_ticket.html', {'categories': categories})



@login_required
def close_ticket(request, ticket_id):
    user = request.user
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Verifica se o usuário tem permissão para fechar
    if not TicketAllowedResponder.objects.filter(user=user).exists():
        msg.error(request, "Você não tem permissão para fechar este ticket.")
        return redirect('ticket_detail', ticket_id=ticket.id)

    ticket.status = 'fechado'
    ticket.save()
    msg.success(request, "Ticket fechado com sucesso.")
    return redirect('ticket_detail', ticket_id=ticket.id)

