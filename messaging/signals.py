from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, ReceivedMessage
from school.models import Parent

@receiver(post_save, sender=Message)
def distribute_message(sender, instance, **kwargs):
    recipients = set()
    
    # Adicionar os pais de alunos das turmas selecionadas
    for class_obj in instance.classes.all():
        for student in class_obj.students.all():
            for parent in Parent.objects.filter(children=student):
                recipients.add(parent.user)
    
    # Adicionar os pais de alunos das séries selecionadas
    for series_obj in instance.series.all():
        for student in series_obj.student_set.all():
            for parent in Parent.objects.filter(children=student):
                recipients.add(parent.user)
    
    # Adicionar um destinatário individual, se houver
    if instance.individual_recipient:
        recipients.add(instance.individual_recipient)
    
    # Criar registros de recebimento da mensagem
    for recipient in recipients:
        ReceivedMessage.objects.create(message=instance, recipient=recipient)
