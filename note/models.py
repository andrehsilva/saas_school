from django.db import models
from django.contrib.auth.models import User
from school.models import Student, Subject

class Note(models.Model):
    # Definindo as opções de período de avaliação
    EVALUATION_PERIOD_CHOICES = [
        ('livre','Livre'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
        ('mensal', 'Mensal'),
        ('quadremestral', 'Quadremestral'),
        ('contínua', 'Contínua'),
        ('unidade', 'Por Unidade'),
    ]
    
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE,
        verbose_name="Aluno"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Disciplina"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Título"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrição"
    )
    performance = models.TextField(
        blank=True,
        null=True,
        verbose_name="Desempenho"
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True, blank=True,
        verbose_name="Nota"
    )
    weight = models.IntegerField(
        default=1,
        verbose_name="Peso"
    )
    date = models.DateField(
        verbose_name="Data"
    )
    evaluation_period = models.CharField(
        max_length=20,
        choices=EVALUATION_PERIOD_CHOICES,
        default='bimestral',  # Definindo Bimestral como padrão
        verbose_name="Período de Avaliação"
    )
    attachment = models.FileField(
        upload_to='note_attachments/',
        blank=True,
        null=True,
        verbose_name="Anexo",
        help_text="Arquivo opcional enviado com a mensagem."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )

    def __str__(self):
        return f"{self.student} - {self.title}"

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
