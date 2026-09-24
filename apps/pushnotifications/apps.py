from django.apps import AppConfig


class Config(AppConfig):
    name = 'apps.pushnotifications'
    label = 'a4_candy_pushnotifications'

    def ready(self):
        from . import signals  # noqa: F401
