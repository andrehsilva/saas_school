from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from school.models import Grade, Class  # Importação das models corretas

class Category(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nome"),
        help_text=_("Nome da categoria (ex: Matemática, Ciências, Jogos Educativos).")
    )

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'collection'
        verbose_name = _("Categoria")
        verbose_name_plural = _("Categorias")


class CollectionItem(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name=_("Título"),
        help_text=_("Título do conteúdo ou jogo.")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Descrição"),
        help_text=_("Descrição opcional do conteúdo ou jogo.")
    )
    html_path = models.CharField(
        max_length=255,
        help_text=_("Ex: collections/html/nome_da_pasta/index.html"),
        verbose_name=_("Caminho HTML")
    )
    thumbnail = models.ImageField(
        upload_to='collections/thumbs/',
        blank=True,
        null=True,
        verbose_name=_("Miniatura"),
        help_text=_("Imagem de capa ou miniatura do conteúdo.")
    )
    categories = models.ManyToManyField(
        Category,
        blank=True,
        verbose_name=_("Categorias"),
        help_text=_("Categorias associadas a este conteúdo.")
    )
    target_grades = models.ManyToManyField(
        Grade,
        blank=True,
        related_name='collections',
        verbose_name=_("Séries Alvo"),
        help_text=_("Séries escolares para as quais este conteúdo é direcionado.")
    )
    target_classes = models.ManyToManyField(
        Class,
        blank=True,
        related_name='collections',
        verbose_name=_("Classes Alvo"),
        help_text=_("Classes escolares específicas que devem receber o conteúdo.")
    )
    target_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='individual_collections',
        verbose_name=_("Usuários Alvo"),
        help_text=_("Usuários específicos que devem receber este conteúdo.")
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Enviado por"),
        help_text=_("Usuário responsável pelo envio do conteúdo.")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de Envio"),
        help_text=_("Data e hora em que o conteúdo foi enviado.")
    )

    class Meta:
        verbose_name = _("Jogo-Coleção")
        verbose_name_plural = _("Jogos-Coleções")

    def __str__(self):
        return self.title

    def get_html_url(self):
        from django.conf import settings
        return f"{settings.MEDIA_URL}{self.html_path}"