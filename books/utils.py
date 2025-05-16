from django.db.models import Q
from books.models import Document
from school.models import GradeCoordinator
from django.utils import timezone
from message.utils import get_user_visibility_context  # Ou copie a função para cá

def get_accessible_documents(user):
    """
    Retorna todos os documentos visíveis ao usuário, baseado em seu papel e relacionamentos.
    """
    context = get_user_visibility_context(user)
    
    # Diretores globais e coordenadores/diretores ativos veem tudo
    if context.get('is_global_director') or context.get('is_coordinator'):
        return Document.objects.all()
    
    # Filtros para outros usuários
    query = Q(target_users=user)  # Documentos direcionados ao usuário
    
    # Documentos para turmas do usuário
    if context["user_classes"].exists():
        query |= Q(target_classes__in=context["user_classes"])
    
    # Documentos para séries do usuário
    if context["user_grades"].exists():
        query |= Q(target_grades__in=context["user_grades"])
    
    return Document.objects.filter(query).distinct()

def has_document_access(user, document):
    """
    Verifica se o usuário tem acesso a um documento específico.
    """
    context = get_user_visibility_context(user)
    
    # Acesso direto ou permissão global
    if document.target_users.filter(id=user.id).exists():
        return True
    if context.get('is_global_director') or context.get('is_coordinator'):
        return True
    
    # Acesso via turmas/séries
    if document.target_classes.filter(id__in=context["user_classes"]).exists():
        return True
    if document.target_grades.filter(id__in=context["user_grades"]).exists():
        return True
    
    return False