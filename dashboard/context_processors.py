from school.models import UserRole

def user_roles(request):
    if request.user.is_authenticated:
        roles = (
            UserRole.objects
            .filter(user=request.user)
            .select_related("role")
            .values_list("role__name", flat=True)
        )
        return {"user_roles": list(roles)}
    return {"user_roles": []}
