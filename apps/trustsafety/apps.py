from django.apps import AppConfig


class Config(AppConfig):
    name = 'apps.trustsafety'
    label = 'a4_candy_trustsafety'

    def ready(self):
        from . import signals  # noqa: F401
