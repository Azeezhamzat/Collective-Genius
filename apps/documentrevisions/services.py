"""Bridges Paragraph/ParagraphRevision to the pure-Python diff engine."""

from . import engine
from .models import ParagraphRevision


def history_for_paragraph(paragraph):
    """Every revision of ``paragraph``, most recent first, each
    annotated with ``.is_trivial`` against the text that replaced it
    (the paragraph's current text for the newest revision, or the next
    -- more recent -- revision's text otherwise).
    """
    revisions = list(
        ParagraphRevision.objects.filter(paragraph=paragraph))
    newer_text = paragraph.text
    for revision in revisions:
        revision.is_trivial = engine.is_trivial_edit(
            revision.text, newer_text)
        newer_text = revision.text
    return revisions
