from django.db import models
import uuid
from django.conf import settings


class CallToAction(models.Model):
    title = models.CharField(
        max_length=255, 
        default="Fique por dentro das novidades!",
        verbose_name='Título',
        help_text='Digite um título chamativo para a chamada de atenção.'
    )
    description = models.TextField(
        default="Confira os últimos artigos e não perca as atualizações mais importantes.",
        verbose_name='Descrição',
        help_text='Escreva um texto breve que descreva a chamada.'
    )
    btn_texto = models.CharField(
        max_length=50, 
        default="Ver Artigos →",
        verbose_name='Texto do Botão',
        help_text='Texto que aparecerá no botão de ação (ex: "Ver mais").'
    )
    btn_link = models.URLField(
        default="#blog",
        verbose_name='Link do Botão',
        help_text='URL de destino ao clicar no botão.'
    )
    image = models.ImageField(
        upload_to='cta_images/', 
        blank=True, 
        null=True,
        verbose_name='Imagem',
        help_text='Imagem opcional para ilustrar a chamada.'
    )
    active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Marque para exibir essa chamada no site.'
    )

    def __str__(self):
        return self.title


class Category(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name='Nome',
        help_text='Nome da categoria do blog.'
    )
    description = models.TextField(
        null=True, 
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição opcional sobre a categoria.'
    )

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.name


class Blog(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name='Autor',
        help_text='Usuário responsável pela publicação.'
    )
    name = models.CharField(
        max_length=255, 
        verbose_name='Título',
        help_text='Título da postagem.'
    )
    image = models.ImageField(
        null=True, 
        blank=True, 
        #default="default.jpg", 
        upload_to='images/',  
        verbose_name='Imagem',
        help_text='Imagem de capa da postagem.'
    )
    short_description = models.CharField(
        max_length=2000, 
        null=True, 
        blank=True, 
        verbose_name='Descrição Curta',
        help_text='Resumo breve da postagem (aparece em listagens ou destaques).'
    )
    description = models.TextField(
        null=True, 
        blank=True,
        verbose_name='Descrição',
        help_text='Conteúdo principal da postagem.'
    )
    categories = models.ManyToManyField(
        'Category', 
        blank=True,
        verbose_name='Categorias',
        help_text='Selecione uma ou mais categorias para classificar a postagem.'
    )
    created = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Data de Criação',
        help_text='Data e hora em que a postagem foi criada.'
    )
    star = models.BooleanField(
        default=False, 
        verbose_name='Especial',
        help_text='Marque se esta postagem for um destaque ou recomendada.'
    )
    active = models.BooleanField(
        default=True, 
        verbose_name='Ativo',
        help_text='Marque para que a postagem apareça no site.'
    )
    id = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        primary_key=True, 
        editable=False,
        verbose_name='ID',
        help_text='Identificador único da postagem (não editável).'
    )

    class Meta:
        verbose_name = "Postagem"
        verbose_name_plural = "Postagens"

    def __str__(self):
        return self.name
