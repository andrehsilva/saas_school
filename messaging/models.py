from django.db import models
from django.conf import settings
from school.models import Class, Series, UserRole  # Importando o modelo de turmas e séries
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='messages/', null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)
    classes = models.ManyToManyField(Class, related_name='messages', blank=True)  # Relacionando com turmas
    series = models.ManyToManyField(Series, related_name='messages', blank=True)  # Relacionando com séries inteiras
    individual_recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='direct_messages',
        null=True, blank=True
    )  # Permitir envio direto para um pai

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Verifica se o remetente tem permissão para enviar mensagens
        if not UserRole.objects.filter(user=self.sender, can_send_messages=True).exists():
            raise ValidationError("Você não tem permissão para enviar mensagens.")
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ['-created_at']

class ReceivedMessage(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='received_messages')
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    read = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient.username} - {self.message.title}"

    class Meta:
        verbose_name = "Mensagem Recebida"
        verbose_name_plural = "Mensagens Recebidas"
        ordering = ['-received_at']
