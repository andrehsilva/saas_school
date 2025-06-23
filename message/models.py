# message/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from school.models import Class, Grade
from django.urls import reverse


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
        help_text=_("Título da mensagem."),
        blank=True,
        null=True
    )
    context = models.TextField(
        verbose_name=_("Conteúdo"),
        help_text=_("Conteúdo da mensagem."),
        blank=True,
        null=True
    )
    activities = models.TextField(
        verbose_name=_("Atividades na Classe"),
        help_text=_("Atividades realizadas na classe (para mensagens de rotina diária)."),
        blank=True,
        null=True
    )
    homework = models.TextField(
        verbose_name=_("Tarefa de Casa"),
        help_text=_("Tarefa de casa (para mensagens de rotina diária)."),
        blank=True,
        null=True
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
        editable=True,
        related_name='messages',
        verbose_name=_("Criada por"),
        help_text=_("Usuário responsável pela criação da mensagem.")
    )
    grades = models.ManyToManyField(
        'school.Grade',
        blank=True,
        related_name='messages',
        verbose_name=_("Séries"),
        help_text=_("Séries para as quais a mensagem será enviada.")
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
    # Remove a imagem de capa do modelo Message
    # image = models.ImageField(
    #     upload_to='messages/',
    #     null=True,
    #     blank=True,
    #     verbose_name=_("Imagem"),
    #     help_text=_("Imagem associada à mensagem (opcional).")
    # )
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
    scheduled_time = models.DateTimeField(
        verbose_name=_("Data e Hora Agendada"),
        help_text=_("Data e hora em que a mensagem estará disponível."),
        blank=True,
        null=True
    )

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('message:message_detail', args=['message', self.id])

    class Meta:
        verbose_name = _("Mensagem")
        verbose_name_plural = _("Mensagens")


class MessageImage(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='gallery_images', # Usamos related_name para acessar as imagens de uma mensagem
        verbose_name=_("Mensagem")
    )
    image = models.ImageField(
        upload_to='message_gallery/', # Novo diretório para as imagens da galeria
        verbose_name=_("Imagem")
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Descrição da Imagem")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de Upload")
    )

    def __str__(self):
        return f"Imagem para '{self.message.title}'"

    class Meta:
        verbose_name = _("Imagem da Mensagem")
        verbose_name_plural = _("Imagens da Mensagem")
        ordering = ['uploaded_at'] # Opcional: ordenar as imagens por data de upload


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


class Event(models.Model):
    titulo = models.CharField(max_length=200)
    inicio = models.DateTimeField()
    fim = models.DateTimeField(null=True, blank=True)
    classes = models.ManyToManyField('school.Class', related_name='events')

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _("Evento")
        verbose_name_plural = _("Eventos")