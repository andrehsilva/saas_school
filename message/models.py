# message/models.py
from django.db import models
from django.contrib.auth.models import User
from school.models import Class  # Certifique-se de importar a Classe corretamente do app 'school'
from django.db.models import Q



class MessageType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    color = models.CharField(max_length=7, default="#000000")  # Cor em formato HEX

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Mensagem"
        verbose_name_plural = "Tipos de Mensagens"


class Message(models.Model):
    title = models.CharField(max_length=255)
    context = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='messages')
    classes = models.ManyToManyField(Class, related_name='messages', blank=True)
    users = models.ManyToManyField(User, related_name='individual_messages', blank=True)
    image = models.ImageField(upload_to='messages/', null=True, blank=True)
    attachments = models.FileField(upload_to='attachments/', null=True, blank=True)
    type = models.ForeignKey(MessageType, on_delete=models.SET_NULL, null=True, blank=True)
   
    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"




class ReceivedMessage(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    message = models.ForeignKey('Message', on_delete=models.CASCADE, related_name="received_by")
    read = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient.username} - {self.message.title}"
    

class MessageReadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    read = models.BooleanField(default=True)  # Sempre será True ao marcar como lida
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'message')  # Evita duplicação de registros



