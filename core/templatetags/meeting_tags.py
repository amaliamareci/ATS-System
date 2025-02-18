from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def filter_by_status(processes, status):
    return [p for p in processes if p.status == status]

@register.filter(name='format_status')
def format_status(value):
    if value:
        return value.replace('_', ' ').title()
    return value 