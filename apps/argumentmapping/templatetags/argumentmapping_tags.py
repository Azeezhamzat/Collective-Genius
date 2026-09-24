from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Look up ``key`` in ``dictionary`` from a template (Django templates
    can only do ``dict.key`` for literal string keys, not a variable
    key)."""
    if not dictionary:
        return None
    return dictionary.get(key)
