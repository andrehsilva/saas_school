from django.db import models
import uuid
from django.contrib.auth.models import User
from django.conf import settings



# Create your models here.

class CallToAction(models.Model):
    title = models.CharField(max_length=255, default="Fique por dentro das novidades!")
    description = models.TextField(default="Confira os últimos artigos e não perca as atualizações mais importantes.")
    btn_texto = models.CharField(max_length=50, default="Ver Artigos →")
    btn_link = models.URLField(default="#blog")
    image = models.ImageField(upload_to='cta_images/', blank=True, null=True)  # Novo campo para imagem
    active = models.BooleanField(default=True)  # Campo para controle de ativo/desativo


    def __str__(self):
        return self.title
    

    
class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = ("Categoria")
        verbose_name_plural = ("Categorias")

    def __str__(self):
        return self.name
    



class Blog(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Autor')
    name = models.CharField(max_length=255, verbose_name='Título')
    image = models.ImageField(
        null=True, blank=True, default="default.jpg", upload_to='images/',  verbose_name='Imagem')
    short_description = models.CharField(max_length=2000, null=True, blank=True, verbose_name='Descrição Curta')
    description = models.TextField(null=True, blank=True,verbose_name='Descrição')
    categories = models.ManyToManyField('Category', blank=True , verbose_name='Categorias' )
    created = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    star = models.BooleanField(default=False, verbose_name='Especial')  # Campo para controle de especial
    active = models.BooleanField(default=True, verbose_name='Ativo')  # Campo para controle de ativo/desativo
    id = models.UUIDField(default = uuid.uuid4, unique=True, 
                        primary_key=True, editable=False)

    class Meta:
        verbose_name = ("Postagem")
        verbose_name_plural = ("Postagens")

    def __str__(self):
        return self.name