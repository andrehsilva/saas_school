from django.db import models
from django.contrib.auth.models import User
from school.models import Grade, Class

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'collection'
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

class CollectionItem(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    html_path = models.CharField(max_length=255, help_text="Ex: collections/html/nome_da_pasta/index.html")
    thumbnail = models.ImageField(upload_to='collections/thumbs/', blank=True, null=True)
    categories = models.ManyToManyField(Category, blank=True)
    target_grades = models.ManyToManyField(Grade, blank=True, related_name='collections')
    target_classes = models.ManyToManyField(Class, blank=True, related_name='collections')
    target_users = models.ManyToManyField(User, blank=True, related_name='individual_collections')

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Jogo-Coleção"
        verbose_name_plural = "Jogos-Coleções"

    def __str__(self):
        return self.title

    def get_html_url(self):
        from django.conf import settings
        return f"{settings.MEDIA_URL}{self.html_path}"



class Grade(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class SchoolClass(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name