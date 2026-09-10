from django import template
import os

register = template.Library()


@register.filter
def basename(value):
    """Return the basename of a file path"""
    if value:
        return os.path.basename(str(value))
    return ""


@register.filter
def split(value, arg):
    """Split a string by a delimiter and return as list"""
    if value:
        return str(value).split(arg)
    return []
