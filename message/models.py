from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from school.models import Class


class MessageType(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Nome"),
        help_text=_("Nome do tipo de mensagem (ex: Aviso, Recado, Urgente).")
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Descrição"),
        help_text=_("Descrição opcional do tipo de mensagem.")
    )
    color = models.CharField(
        max_length=7,
        default="#000000",
        verbose_name=_("Cor"),
        help_text=_("Cor associada ao tipo de mensagem (formato HEX, ex: #FF0000).")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Tipo de Mensagem")
        verbose_name_plural = _("Tipos de Mensagens")


class Message(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name=_("Título"),
        help_text=_("Título da mensagem.")
    )
    context = models.TextField(
        verbose_name=_("Conteúdo"),
        help_text=_("Conteúdo da mensagem.")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de Criação"),
        help_text=_("Data e hora em que a mensagem foi criada.")
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='messages',
        verbose_name=_("Criada por"),
        help_text=_("Usuário responsável pela criação da mensagem.")
    )
    classes = models.ManyToManyField(
        Class,
        blank=True,
        related_name='messages',
        verbose_name=_("Turmas"),
        help_text=_("Turmas para as quais a mensagem será enviada.")
    )
    users = models.ManyToManyField(
        User,
        blank=True,
        related_name='individual_messages',
        verbose_name=_("Usuários"),
        help_text=_("Usuários específicos que receberão a mensagem.")
    )
    image = models.ImageField(
        upload_to='messages/',
        null=True,
        blank=True,
        verbose_name=_("Imagem"),
        help_text=_("Imagem associada à mensagem (opcional).")
    )
    attachments = models.FileField(
        upload_to='attachments/',
        null=True,
        blank=True,
        verbose_name=_("Anexo"),
        help_text=_("Arquivo anexo à mensagem (opcional).")
    )
    type = models.ForeignKey(
        MessageType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Tipo"),
        help_text=_("Tipo de mensagem (ex: Aviso, Urgente, Informação).")
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Mensagem")
        verbose_name_plural = _("Mensagens")


class ReceivedMessage(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_messages",
        verbose_name=_("Destinatário"),
        help_text=_("Usuário que recebeu a mensagem.")
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="received_by",
        verbose_name=_("Mensagem"),
        help_text=_("Mensagem recebida.")
    )
    read = models.BooleanField(
        default=False,
        verbose_name=_("Lida"),
        help_text=_("Indica se a mensagem foi lida pelo destinatário.")
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de Recebimento"),
        help_text=_("Data em que a mensagem foi disponibilizada.")
    )

    def __str__(self):
        return f"{self.recipient.username} - {self.message.title}"

    class Meta:
        verbose_name = _("Recebida")
        verbose_name_plural = _("Recebidas")


class MessageReadLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Usuário"),
        help_text=_("Usuário que leu a mensagem.")
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name=_("Mensagem"),
        help_text=_("Mensagem que foi lida.")
    )
    read = models.BooleanField(
        default=True,
        verbose_name=_("Lida"),
        help_text=_("Indica se a mensagem foi lida (sempre True).")
    )
    read_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de Leitura"),
        help_text=_("Data e hora da leitura.")
    )

    class Meta:
        verbose_name = _("Log de Leitura")
        verbose_name_plural = _("Logs de Leitura")
        unique_together = ('user', 'message')
