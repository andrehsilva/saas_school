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
    description = models.TextField(
        _("Descrição"),
        blank=True,
        null=True,
        help_text=_("Descrição opcional do papel.")
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
        verbose_name = _("Papel Geral do Usuário")
        verbose_name_plural = _("Papéis Gerais dos Usuários")
        unique_together = ('user', 'role')


class Grade(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Nome da Série"),
        help_text=_("Ex: 1º Ano, 6ª Série")
    )
    # Coordenadores e diretores diretamente vinculados à série
    coordinators = models.ManyToManyField(
        User,
        blank=True,
        related_name='coordinated_grades',
        verbose_name=_("Coordenadores"),
        help_text=_("Usuários com papel de coordenação nesta série")
    )
    directors = models.ManyToManyField(
        User,
        blank=True,
        related_name='directed_grades',
        verbose_name=_("Diretores de Série"),
        help_text=_("Usuários com papel de direção nesta série")
    )

    colaborator = models.ManyToManyField(
        User,
        blank=True,
        related_name='colaborated_grades',
        verbose_name=_("Colaboradores de Série"),
        help_text=_("Usuários com papel de colaborador nesta série")
    )
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Série")
        verbose_name_plural = _("Séries")


class Class(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name=_("Turma"),
        help_text=_("Identificador único da turma (ex: Turma A, 6º Ano B).")
    )
    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE,
        related_name='classrooms',
        verbose_name=_("Série"),
        help_text=_("Séries escolares associada à turma.")
    )
    teachers = models.ManyToManyField(
        User,
        related_name='classrooms_taught',
        verbose_name=_("Professores"),
        help_text=_("Professores responsáveis por esta turma.")
    )
    is_regular = models.BooleanField(
        default=True,
        verbose_name=_("Turma Regular"),
        help_text=_("Indica se esta é uma turma regular.")
    )
    academic_year = models.PositiveSmallIntegerField(
        default=timezone.now().year,
        verbose_name=_("Ano Letivo"),
        help_text=_("Ano de referência para a turma.")
    )

    def __str__(self):
        return f"{self.grade.name} - {self.name} ({self.academic_year})"
    

    def get_all_members(self):
        members = list(self.teachers.all())
        members += [student.user for student in self.students.all()]
        members += list(self.grade.coordinators.all())
        members += list(self.grade.directors.all())
        return list(set(members))
    
    class Meta:
        verbose_name = _("Turma")
        verbose_name_plural = _("Turmas")
        unique_together = ('name', 'grade', 'academic_year')


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Usuário"),
        help_text=_("Usuário correspondente ao aluno.")
    )
    classes_assigned = models.ManyToManyField(
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


class Parent(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        verbose_name=_("Usuário")
    )
    children = models.ManyToManyField(
        Student,
        related_name='parents',
        verbose_name=_("Filhos")
    )

    def __str__(self):
        return f"Responsável: {self.user.get_full_name()}"

    class Meta:
        verbose_name = _("Pai/Mãe")
        verbose_name_plural = _("Pais")


class Subject(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nome da Disciplina"),
        help_text=_("Nome da disciplina, como Matemática, História ou Ciências.")
    )

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _("Disciplina")
        verbose_name_plural = _("Disciplinas")
        unique_together = (("name",),)
