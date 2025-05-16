from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _



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
        verbose_name = _("Papel do Usuário")
        verbose_name_plural = _("Papéis dos Usuários")
        unique_together = ('user', 'role')


# Série
class Grade(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name=_("Nome da Série"),
        help_text=_("Nome da série escolar (ex: 1º Ano, 6ª Série).")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Série")
        verbose_name_plural = _("Séries")


# Classe
class Class(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name=_("Nome da Classe"),
        help_text=_("Nome ou código identificador da classe (ex: Turma A, 6B).")
    )
    grade = models.ForeignKey(
        Grade, 
        on_delete=models.CASCADE,
        verbose_name=_("Série"),
        help_text=_("Série escolar associada à classe.")
    )
    teachers = models.ManyToManyField(
        User, 
        related_name='classes_taught',
        verbose_name=_("Professores"),
        help_text=_("Professores responsáveis por esta classe.")
    )
    is_regular = models.BooleanField(
        default=True,
        verbose_name=_("Classe Regular"),
        help_text=_("Indica se esta classe é uma classe regular.")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Classe")
        verbose_name_plural = _("Classes")


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


# Alunos
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
        verbose_name=_("Classes"),
        help_text=_("Classes nas quais o aluno está matriculado.")
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