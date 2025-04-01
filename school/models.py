from django.db import models
from django.contrib.auth.models import User

# Papéis (Roles)
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Papel"
        verbose_name_plural = "Papéis"

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
    teacher = models.ForeignKey(User, related_name='classes_taught', on_delete=models.SET_NULL, null=True)

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
    class_assigned = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='students')

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
