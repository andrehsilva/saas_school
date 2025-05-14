from django.db import models
from django.contrib.auth.models import User
from school.models import Parent

class TicketCategory(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome da categoria",
        help_text="Nome identificador da categoria de ticket."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de criação"
    )

    class Meta:
        verbose_name = "Categoria de Ticket"
        verbose_name_plural = "Categorias de Ticket"
        ordering = ['name']

    def __str__(self):
        return self.name

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Aberto'),
        ('in_progress', 'Em andamento'),
        ('closed', 'Fechado'),
    ]

    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name="Responsável",
        help_text="Responsável que abriu o ticket."
    )
    subject = models.CharField(
        max_length=255,
        verbose_name="Assunto",
        help_text="Assunto principal do ticket."
    )
    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default='Acadêmico/Pedagógico',
        related_name='tickets',
        verbose_name="Categoria",
        help_text="Categoria à qual o ticket pertence."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de criação"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name="Status",
        help_text="Status atual do ticket."
    )
    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número do ticket",
        help_text="Número único de identificação do ticket."
    )

    def __str__(self):
        return f"Ticket #{self.ticket_number} - {self.subject}"

class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Ticket",
        help_text="Ticket ao qual esta mensagem pertence."
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Remetente",
        help_text="Usuário que enviou a mensagem."
    )
    message = models.TextField(
        verbose_name="Mensagem",
        help_text="Conteúdo da mensagem enviada."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de envio"
    )
    attachment = models.FileField(
        upload_to='ticket_attachments/',
        blank=True,
        null=True,
        verbose_name="Anexo",
        help_text="Arquivo opcional enviado com a mensagem."
    )

    def __str__(self):
        return f"Mensagem de {self.sender} em {self.created_at}"

class TicketAllowedResponder(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuário",
        help_text="Usuário autorizado a responder tickets."
    )
    categories = models.ManyToManyField(
        TicketCategory,
        related_name="allowed_responders",
        verbose_name="Categorias permitidas",
        help_text="Categorias que este usuário pode responder."
    )

    def __str__(self):
        return f"{self.user.username} pode responder tickets"
    
    class Meta:
        verbose_name = ("Permissão de resposta")
        verbose_name_plural = ("Permissões de respostas")
