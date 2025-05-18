from django import template
from message.models import Message
from notification.models import Notification

register = template.Library()

@register.filter
def is_message(value):
    return isinstance(value, Message)

@register.filter
def get_type(value):
    return 'message' if isinstance(value, Message) else 'notification'
