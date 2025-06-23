from django.db.models import Q
from .models import CollectionItem
from message.utils import get_user_visibility_context


def get_accessible_collections(user):
    context = get_user_visibility_context(user)
    query = Q()

    if context["is_global_director"]:
        return CollectionItem.objects.all()

    if context["has_coordination_role"]:
        return CollectionItem.objects.filter(
            Q(target_grades__in=context["user_grades"]) |
            Q(target_classes__in=context["user_classes"])
        ).distinct()

    query |= Q(target_users=user)
    
    if context["student_user_ids"]:
        query |= Q(target_users__id__in=context["student_user_ids"])

    if context["user_classes"]:
        query |= Q(target_classes__in=context["user_classes"])

    if context["user_grades"]:
        query |= Q(target_grades__in=context["user_grades"])

    return CollectionItem.objects.filter(query).distinct()


def has_access(user, item):
    context = get_user_visibility_context(user)

    if context["is_global_director"]:
        return True

    if context["has_coordination_role"]:
        return (
            item.target_grades.filter(id__in=context["user_grades"]).exists() or
            item.target_classes.filter(id__in=context["user_classes"]).exists()
        )

    if item.target_users.filter(id=user.id).exists():
        return True

    if context["student_user_ids"] and item.target_users.filter(id__in=context["student_user_ids"]).exists():
        return True

    return (
        (context["user_classes"] and item.target_classes.filter(id__in=context["user_classes"]).exists()) or
        (context["user_grades"] and item.target_grades.filter(id__in=context["user_grades"]).exists())
    )