from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as msg
from django.db.models import Q
from .models import Ticket, TicketMessage, TicketAllowedResponder
from school.models import Parent
from django.utils.crypto import get_random_string
from django.shortcuts import redirect
from .models import Ticket, TicketAllowedResponder


def generate_ticket_number():
    return get_random_string(8).upper()

@login_required
def ticket_list(request):
    user = request.user
    try:
        parent = Parent.objects.get(user=user)
        tickets = Ticket.objects.filter(parent=parent).order_by('-created_at')
    except Parent.DoesNotExist:
        if TicketAllowedResponder.objects.filter(user=user).exists():
            tickets = Ticket.objects.all().order_by('-created_at')
        else:
            tickets = Ticket.objects.none()
    
    return render(request, 'ticket/ticket_list.html', {
        'tickets': tickets
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

    if request.method == 'POST' and ticket.status != 'fechado':
        message = request.POST.get('message')
        attachment = request.FILES.get('attachment')

        if message:
            TicketMessage.objects.create(
                ticket=ticket,
                sender=user,
                message=message,
                attachment=attachment
            )
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

    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        attachment = request.FILES.get('attachment')

        if subject and message:
            ticket = Ticket.objects.create(
                parent=parent,
                subject=subject,
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

    return render(request, 'ticket/create_ticket.html')

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