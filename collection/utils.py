# collection/utils.py
from django.db.models import Q
from .models import CollectionItem
from message.utils import get_user_visibility_context

def get_accessible_collections(user):
    """
    Retorna itens de coleção baseados na hierarquia:
    Diretor > Coordenador > Professor > Pais/Alunos
    """
    context = get_user_visibility_context(user)
    query = Q()

    # Diretores globais veem tudo
    if context["is_global_director"]:
        return CollectionItem.objects.all()
    
    # Coordenadores veem apenas suas séries
    if context["has_coordination_role"]:
        query |= Q(target_grades__in=context["user_grades"])
        return CollectionItem.objects.filter(query).distinct()
    
    # Mensagens diretas ao usuário ou seus dependentes (para pais)
    query |= Q(target_users=user) | Q(target_users__id__in=context["student_user_ids"])
    
    # Itens para turmas do usuário
    if context["user_classes"].exists():
        query |= Q(target_classes__in=context["user_classes"])
    
    # Itens para séries do usuário
    if context["user_grades"].exists():
        query |= Q(target_grades__in=context["user_grades"])
    
    return CollectionItem.objects.filter(query).distinct()

def has_access(user, item):
    """
    Verifica acesso considerando todas as camadas hierárquicas
    """
    context = get_user_visibility_context(user)
    
    # Acesso total para diretores/coordenadores
    if context["is_global_director"] or context["has_coordination_role"]:
        return True
    
    # Acesso direto via usuário ou dependentes
    if item.target_users.filter(id__in=[user.id] + context["student_user_ids"]).exists():
        return True
    
    # Acesso via turmas/séries
    return (
        item.target_classes.filter(id__in=context["user_classes"]).exists() or
        item.target_grades.filter(id__in=context["user_grades"]).exists()
    )