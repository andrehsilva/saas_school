from django.db import models
from django.contrib.auth.models import User

# Papéis (Roles)
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    can_send_messages = models.BooleanField(default=False)  # Campo que define se o role pode enviar mensagens

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Permissão por perfil"
        verbose_name_plural = "Permissão por perfil"



# Modelo intermediário para associar User a Role
class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    can_send_messages = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
    
    class Meta:
        verbose_name_plural = "Associar usuário com função"
    
    


# Série
class Series(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Série"
        verbose_name_plural = "Séries"

# Classe
class Class(models.Model):
    name = models.CharField(max_length=50)
    series = models.ForeignKey(Series, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, related_name='classes_taught', on_delete=models.SET_NULL, null=True)
    students = models.ManyToManyField(User, related_name='enrolled_classes')

    def teacher_full_name(self):
        try:
            teacher = User.objects.get(id=self.teacher_id)
            return f"{teacher.first_name} {teacher.last_name}"
        except User.DoesNotExist:
            return "Professor não encontrado"
    
    teacher_full_name.short_description = "Nome do professor"

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"


# Pais
class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    children = models.ManyToManyField(User, related_name='parent_of')

    def __str__(self):
        return f"Parent of {', '.join([child.username for child in self.children.all()])}"
    
    class Meta:
        verbose_name = "Pai/Mãe"
        verbose_name_plural = "Pais"

# Alunos
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    series = models.ForeignKey(Series, on_delete=models.SET_NULL, null=True)
    classes = models.ManyToManyField(Class, related_name='students_in_class')

    def __str__(self):
        return self.user.username
    
    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
