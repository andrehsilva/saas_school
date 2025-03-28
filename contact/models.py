from django.db import models

class Contato(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome')
    email = models.EmailField(verbose_name='E-mail')
    mensage = models.TextField(verbose_name='Mensagem')
    phone = models.CharField(max_length=15, default="", verbose_name='Telefone')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Criado em:')

    def __str__(self):
        return self.name
