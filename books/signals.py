# books/signals.py

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Category

@receiver(post_migrate)
def create_default_book_categories(sender, **kwargs):
    """Cria categorias padrão para documentos após migração do app 'books'."""
    if sender.name == 'books':
        default_categories = [
            "Literatura",
            "Matemática",
            "História",
            "Geografia",
            "Ciências",
            "Física",
            "Química",
            "Biologia",
            "Gramática",
            "Redação",
            "Filosofia",
            "Sociologia",
            "Arte",
            "Educação Física",
            "Inglês",
            "Espanhol",
            "Religião",
            "Atualidades",
            "Projetos",
            "Manual do Aluno",
            "Manual da escola"
        ]

        for category_name in default_categories:
            Category.objects.get_or_create(name=category_name)
