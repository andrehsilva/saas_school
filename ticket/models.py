from django.db import models
from django.contrib.auth.models import User
from school.models import Parent

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Aberto'),
        ('in_progress', 'Em andamento'),
        ('closed', 'Fechado'),
    ]

    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    ticket_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"Ticket #{self.ticket_number} - {self.subject}"

class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='ticket_attachments/', blank=True, null=True)

    def __str__(self):
        return f"Mensagem de {self.sender} em {self.created_at}"

class TicketAllowedResponder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Você pode adicionar filtros por escola se necessário

    def __str__(self):
        return f"{self.user.username} pode responder tickets"

