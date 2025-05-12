# navigation/templatetags/navigation_tags.py
from django import template
from navigator.models import NavigationLink

register = template.Library()

@register.simple_tag
def get_nav_links():
    return NavigationLink.objects.filter(is_active=True).order_by('order')