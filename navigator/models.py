# navigation/models.py
from django.db import models

class NavigationLink(models.Model):
    title = models.CharField(max_length=50)
    url = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    objects = models.Manager()  # Adicione esta linha
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
    
        
   