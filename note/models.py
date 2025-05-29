from django.db import models
from django.contrib.auth.models import User
from school.models import Student, Subject

class Note(models.Model):
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
        verbose_name="Aluno",
        help_text="Selecione o aluno a quem a nota pertence."
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Disciplina",
        help_text="Informe a disciplina relacionada à nota. Pode ser deixado em branco se não aplicável."
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Título",
        help_text="Título identificador da nota ou atividade avaliada."
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrição",
        help_text="Descrição adicional sobre a nota ou atividade (opcional)."
    )
    performance = models.TextField(
        blank=True,
        null=True,
        verbose_name="Desempenho",
        help_text="Detalhes sobre o desempenho do aluno nesta avaliação (opcional)."
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True, blank=True,
        verbose_name="Nota",
        help_text="Valor numérico da nota atribuída. Use ponto para separar casas decimais (ex: 8.75)."
    )
    weight = models.IntegerField(
        default=1,
        verbose_name="Peso",
        help_text="Peso da nota no cálculo final. Por padrão, é 1."
    )
    date = models.DateField(
        verbose_name="Data",
        help_text="Data em que a avaliação foi aplicada ou registrada."
    )
    evaluation_period = models.CharField(
        max_length=20,
        choices=EVALUATION_PERIOD_CHOICES,
        default='bimestral',
        verbose_name="Período de Avaliação",
        help_text="Selecione o período de avaliação relacionado à nota."
    )
    attachment = models.FileField(
        upload_to='note_attachments/',
        blank=True,
        null=True,
        verbose_name="Anexo",
        help_text="Arquivo opcional enviado com a nota, como provas ou atividades digitalizadas."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
        help_text="Data e hora em que esta nota foi registrada no sistema."
    )

    def __str__(self):
        return f"{self.student} - {self.title}"

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
