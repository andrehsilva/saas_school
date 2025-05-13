# navigation/models.py
from django.db import models

class NavigationLink(models.Model):
    title = models.CharField(max_length=50,
                              verbose_name=("Título do Link"),
                              help_text=("Informe o título do link que aparecerá no header."))
    url = models.CharField(max_length=200,
                              verbose_name=("URL do Link"),
                              help_text=("Informe a URL do link ex: ( / )"))
    is_active = models.BooleanField(default=True,
                              verbose_name=("É ativo?"),
                              help_text=("Habilite ou desabilite o link"))
    order = models.PositiveIntegerField(default=0,
                              verbose_name=("Sequência do Link"),
                              help_text=("Informe a sequência que o link que aparecerá no header."))
    
    objects = models.Manager()  # Adicione esta linha
    
    class Meta:
        ordering = ['order']
        verbose_name = ("Link")
        verbose_name_plural = ("Links")
    

    def __str__(self):
        return self.title
    
        
   