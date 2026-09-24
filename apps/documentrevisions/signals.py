def snapshot_paragraph_revision(sender, instance, **kwargs):
    """Before a Paragraph is saved with changed text, snapshot the text
    it's about to replace, so editing history isn't lost.

    A no-op for a brand new (unsaved) paragraph, and a no-op if the
    text didn't actually change (saving unrelated fields, or an
    identical re-save, shouldn't create a noise revision).
    """
    from .models import ParagraphRevision

    if not instance.pk:
        return

    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if previous.text == instance.text:
        return

    ParagraphRevision.objects.create(
        paragraph=instance, text=previous.text)
