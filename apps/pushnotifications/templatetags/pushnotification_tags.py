from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def vapid_public_key():
    """The VAPID public key a browser needs to create a Web Push
    subscription (``PushManager.subscribe({applicationServerKey: ...})``).
    Empty until a deployment generates a VAPID key pair and sets
    ``A4_VAPID_PUBLIC_KEY`` -- see the comment in settings/base.py.
    """
    return getattr(settings, 'A4_VAPID_PUBLIC_KEY', '')
