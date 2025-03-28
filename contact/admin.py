from django.contrib import admin
from .models import Contato


class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'mensage','created')
    search_fields = ('name', 'email', 'mensage','phone')
    list_filter = ('created',)

admin.site.register(Contato, ContactAdmin)

