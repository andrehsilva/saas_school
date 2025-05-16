from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone



# Papéis (Roles)
class Role(models.Model):
    name = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name=_("Nome"),
        help_text=_("Nome do papel ou função (ex: Professor, Responsável, Aluno).")
    )
    can_post = models.BooleanField(
        default=True,
        verbose_name=_("Pode Postar"),
        help_text=_("Indica se esse papel tem permissão para criar postagens.")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Papel")
        verbose_name_plural = _("Papéis")


# Relacionamento entre Usuário e Papel
class UserRole(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="roles",
        verbose_name=_("Usuário"),
        help_text=_("Usuário associado ao papel.")
    )
    role = models.ForeignKey(
        Role, 
        on_delete=models.CASCADE, 
        related_name="users",
        verbose_name=_("Papel"),
        help_text=_("Papel atribuído ao usuário.")
    )

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

    class Meta:
        verbose_name = "Papel Geral do Usuário"
        verbose_name_plural = "Papéis Gerais dos Usuários"
        unique_together = ('user', 'role')


# Série
class Grade(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name=_("Nome da Série"),
        help_text=_("Nome da série escolar (ex: 1º Ano, 6ª Série).")
    )
    
    coordinators = models.ManyToManyField(
        User,
        through='GradeCoordinator',  # Usando o modelo corrigido
        related_name='coordinated_grades',
        verbose_name=_("Designações")
    )
    class Meta:
        verbose_name = _("Série")
        verbose_name_plural = _("Séries")
        permissions = [
            ("global_director_access", _("Acesso completo de diretor a todas as séries")),
        ]

    def __str__(self):
        return self.name

    def current_coordinators(self):
        return self.grade_coordinators.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )

class GradeCoordinator(models.Model):
    ROLE_CHOICES = (
        ('CO', _('Coordenador')),
        ('DI', _('Diretor de Série')),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Usuário"),
        related_name='grade_coordinations'
    )
    
    grade = models.ForeignKey(  # ForeignKey para Grade
        Grade,
        on_delete=models.CASCADE,
        verbose_name=_("Série"),
        related_name='grade_coordinators'
    )
    
    role = models.CharField(
        max_length=2,
        choices=ROLE_CHOICES,
        default='CO',
        verbose_name=_("Tipo de Cargo")
    )
    
    start_date = models.DateField(
        verbose_name=_("Data de Início")
    )
    
    end_date = models.DateField(
        verbose_name=_("Data de Término"),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Designação de Cargo")
        verbose_name_plural = _("Designações de Cargos")
        unique_together = ('user', 'grade', 'role')  # Campos válidos

    def __str__(self):
        return f"{self.user} - {self.get_role_display()} ({self.grade})"
    




class Class(models.Model):  # Nome alterado
    name = models.CharField(
        max_length=50,
        verbose_name=_("Turma"),
        help_text=_("Identificador único da turma (ex: Turma A, 6º Ano B).")  # Ajuste no help_text
    )
    grade = models.ForeignKey(
        Grade, 
        on_delete=models.CASCADE,
        verbose_name=_("Série"),
        related_name='classrooms',  # Novo related_name
        help_text=_("Série escolar associada à turma.")
    )
    teachers = models.ManyToManyField(
        User, 
        related_name='classrooms_taught',  # Atualizado
        verbose_name=_("Professores"),
        help_text=_("Professores responsáveis por esta turma.")
    )
    is_regular = models.BooleanField(
        default=True,
        verbose_name=_("Turma Regular"),
        help_text=_("Indica se esta é uma turma regular.")
    )
    academic_year = models.PositiveSmallIntegerField(  # Novo campo sugerido
        verbose_name=_("Ano Letivo"),
        help_text=_("Ano de referência para a turma"),
        default=timezone.now().year
    )

    def __str__(self):
        return f"{self.grade.name} - {self.name} ({self.academic_year})"  # Melhoria na representação

    class Meta:
        verbose_name = _("Turma")
        verbose_name_plural = _("Turmas")
        unique_together = ('name', 'grade', 'academic_year')  # Garante unicidade


# Pais
class Parent(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='parent_profile',  
        verbose_name=_("Usuário"),
        help_text=_("Usuário do pai, mãe ou responsável.")
    )
    children = models.ManyToManyField(
        'Student', 
        related_name='parents',
        verbose_name=_("Filhos"),
        help_text=_("Alunos associados a este responsável.")
    )

    def __str__(self):
        return f"Parent of {', '.join([child.user.username for child in self.children.all()])}"

    class Meta:
        verbose_name = _("Pai/Mãe")
        verbose_name_plural = _("Pais")


class Student(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        verbose_name=_("Usuário"),
        help_text=_("Usuário correspondente ao aluno.")
    )
    classes_assigned = models.ManyToManyField(  # Nome do campo atualizado
        Class, 
        related_name='students',
        verbose_name=_("Turmas"),
        help_text=_("Turmas nas quais o aluno está matriculado.")
    )

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _("Aluno")
        verbose_name_plural = _("Alunos")


        
class Subject(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nome da Disciplina"),
        help_text=_("Nome da disciplina, como Matemática, História ou Ciências.")
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Código"),
        help_text=_("Código único para a disciplina.")
    )
    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE,
        related_name="subjects",
        verbose_name=_("Série"),
        help_text=_("Série à qual essa disciplina pertence.")
    )
    teachers = models.ManyToManyField(
        User,
        related_name="subjects_taught",
        verbose_name=_("Professores"),
        help_text=_("Professores que lecionam essa disciplina.")
    )

    def __str__(self):
        return f"{self.name} ({self.grade.name})"

    class Meta:
        verbose_name = _("Disciplina")
        verbose_name_plural = _("Disciplinas")
        unique_together = ("name", "grade")