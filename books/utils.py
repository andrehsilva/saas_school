from django.db.models import Q
from books.models import Document
from message.utils import get_user_visibility_context

def get_accessible_documents(user):
    context = get_user_visibility_context(user)
    query = Q()

    # Diretores globais veem tudo
    if context["is_global_director"]:
        return Document.objects.all()
    
    # Coordenadores veem apenas suas séries
    if context["has_coordination_role"]:
        query |= Q(target_grades__in=context["user_grades"])
        return Document.objects.filter(query).distinct()
    
    # Demais regras
    query |= Q(target_users=user) | Q(target_users__id__in=context["student_user_ids"])
    
    if context["user_classes"].exists():
        query |= Q(target_classes__in=context["user_classes"])
    
    if context["user_grades"].exists():
        query |= Q(target_grades__in=context["user_grades"])
    
    return Document.objects.filter(query).distinct()

def has_document_access(user, document):
    context = get_user_visibility_context(user)
    
    if context["is_global_director"]:
        return True
        
    if context["has_coordination_role"]:
        return document.target_grades.filter(id__in=context["user_grades"]).exists()
    
    return (
        document.target_users.filter(id=user.id).exists() or
        document.target_classes.filter(id__in=context["user_classes"]).exists() or
        document.target_grades.filter(id__in=context["user_grades"]).exists()
    )