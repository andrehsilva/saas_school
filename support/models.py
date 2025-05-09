# support/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class TicketStatus(models.TextChoices):
    OPEN = "open", _("Aberto")
    IN_PROGRESS = "in_progress", _("Em andamento")
    CLOSED = "closed", _("Fechado")


class SupportTicket(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name=_("Título"),
        help_text=_("Título do chamado.")
    )
    description = models.TextField(
        verbose_name=_("Descrição"),
        help_text=_("Descrição detalhada do problema ou solicitação.")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de Criação")
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        verbose_name=_("Criado por")
    )
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN,
        verbose_name=_("Status")
    )

    def __str__(self):
        return f"#{self.id} - {self.title}"

    class Meta:
        verbose_name = _("Chamado de Suporte")
        verbose_name_plural = _("Chamados de Suporte")


class SupportMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Chamado")
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Autor")
    )
    message = models.TextField(
        verbose_name=_("Mensagem")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Enviado em")
    )
    attachment = models.FileField(
        upload_to='support_attachments/',
        null=True,
        blank=True,
        verbose_name=_("Anexo")
    )

    def __str__(self):
        return f"{self.author.username} - {self.ticket.title}"

    class Meta:
        verbose_name = _("Mensagem de Suporte")
        verbose_name_plural = _("Mensagens de Suporte")

