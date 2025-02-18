from django import template

register = template.Library()

@register.filter
def call(obj, arg):
    """Call a method with an argument"""
    return obj(arg) 