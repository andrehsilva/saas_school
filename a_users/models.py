from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.conf import settings
import re

# Validador de CPF
def validate_cpf(value):
    if not re.match(r'^\d{11}$', value):
        raise ValidationError("CPF deve ter 11 dígitos numéricos.")



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField(max_length=20, null=True, blank=True)
    cpf = models.CharField(max_length=11, unique=True, null=True, blank=True, validators=[validate_cpf])  # CPF não é obrigatório
    #cpf = models.CharField(max_length=11, unique=True, validators=[validate_cpf])
    phone = models.CharField(max_length=20, blank=True, null=True)
    info = models.TextField(null=True, blank=True) 
    
    def __str__(self):
        return str(self.user)
    
    @property
    def name(self):
        if self.displayname:
            return self.displayname
        return self.user.username 
    
    @property
    def avatar(self):
        if self.image:
            return self.image.url
        return f'{settings.STATIC_URL}images/avatar.svg'
    
    class Meta:
        verbose_name = ("Perfil do usuário")
        verbose_name_plural = ("Perfis de usuários")


