from django.apps import AppConfig


class Config(AppConfig):
    name = 'apps.moderationlog'
    label = 'a4_candy_moderationlog'

    def ready(self):
        from django.db.models.signals import pre_save

        from adhocracy4.comments.models import Comment

        from . import signals
        pre_save.connect(
            signals.log_comment_moderation_changes, sender=Comment)
