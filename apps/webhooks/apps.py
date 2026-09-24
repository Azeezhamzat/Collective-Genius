from django.apps import AppConfig


class Config(AppConfig):
    name = 'apps.webhooks'
    label = 'a4_candy_webhooks'

    def ready(self):
        from . import signals  # noqa: F401
