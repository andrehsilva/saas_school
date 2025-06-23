# message/decorators.py
from functools import wraps
from django.http import HttpResponseForbidden
from .models import Message
from django.shortcuts import render, get_object_or_404

def message_permission_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        message_id = kwargs.get('id') or kwargs.get('message_id')
        message = get_object_or_404(Message, id=message_id)
        user = request.user
        
        has_permission = (
            message.created_by == user or
            message.users.filter(id=user.id).exists() or
            (hasattr(user, 'student') and 
             user.student.classes_assigned.filter(id__in=message.classes.values_list('id', flat=True)).exists()
        ))
        
        if not has_permission:
            return HttpResponseForbidden("Acesso negado")
            
        return view_func(request, *args, **kwargs)

    return _wrapped_view