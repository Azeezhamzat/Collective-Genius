from django.db import models

from apps.documents.models import Paragraph


class ParagraphRevision(models.Model):
    """A snapshot of a Paragraph's text just before it was overwritten
    by an edit -- so a chapter's editing history isn't lost the moment
    someone changes the wording. Not real-time collaborative editing
    (no simultaneous multi-user merge -- see the module docstring in
    apps/documentrevisions/README-shaped comment in
    docs/collective-intelligence-roadmap.md for why that's out of scope
    here), just "what did this used to say."
    """

    paragraph = models.ForeignKey(
        Paragraph, on_delete=models.CASCADE, related_name='revisions')
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return 'Revision of paragraph {} at {}'.format(
            self.paragraph_id, self.created)
