from django.contrib import admin
from .models import *
from django.contrib.admin import AdminSite

# Personalizando o título da página de administração
admin.site.site_title = 'Meu Sistema Escolar'
# Personalizando o nome na barra superior do Django Admin
admin.site.site_header = 'Administração do Sistema Escolar'
# Personalizando o nome do site que aparece no menu do Django Admin
admin.site.index_title = 'Bem-vindo à área administrativa'

admin.site.register(SiteSetting)

