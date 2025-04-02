from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_migrate
from django.dispatch import receiver

# Papéis (Roles)
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    can_post = models.BooleanField(default=True)  # Define se o papel pode postar

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Papel"
        verbose_name_plural = "Papéis"


# Relacionamento entre Usuário e Papel
class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="users")

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

    class Meta:
        verbose_name = "Papel do Usuário"
        verbose_name_plural = "Papéis dos Usuários"
        unique_together = ('user', 'role')  # Evita duplicidade



# Série
class Grade(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Série"
        verbose_name_plural = "Séries"

# Classe
class Class(models.Model):
    name = models.CharField(max_length=50)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    teachers = models.ManyToManyField(User, related_name='classes_taught')  # Permite múltiplos professores
    is_regular = models.BooleanField(default=True)  # Define se a classe é regular

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"

# Pais
class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    children = models.ManyToManyField('Student', related_name='parents')

    def __str__(self):
        return f"Parent of {', '.join([child.user.username for child in self.children.all()])}"

    class Meta:
        verbose_name = "Pai/Mãe"
        verbose_name_plural = "Pais"

# Alunos
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    classes_assigned = models.ManyToManyField(Class, related_name='students')  # Agora um aluno pode estar em várias classes

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"