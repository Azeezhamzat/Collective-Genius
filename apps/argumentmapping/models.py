from django.db import models
from django.utils.translation import gettext_lazy as _

from adhocracy4.comments import models as comment_models


class Stance(models.Model):
    """A comment's author declaring whether their comment supports or
    opposes whatever it's replying to (the debated subject, or a parent
    comment)."""

    SUPPORTS = 'supports'
    OPPOSES = 'opposes'
    STANCE_CHOICES = (
        (SUPPORTS, _('Supports')),
        (OPPOSES, _('Opposes')),
    )

    comment = models.OneToOneField(
        comment_models.Comment,
        on_delete=models.CASCADE,
        related_name='stance',
    )
    value = models.CharField(max_length=16, choices=STANCE_CHOICES)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}: {}'.format(self.comment_id, self.value)
