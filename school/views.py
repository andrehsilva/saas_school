from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required  # garante que só usuários admin possam acessar
def import_users_view(request):
    # Por enquanto só retorna uma resposta simples
    return HttpResponse("Importar Usuários - função ainda não implementada")