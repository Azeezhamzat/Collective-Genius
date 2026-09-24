"""Pure-Python text-change summary for document paragraph revisions.

Uses Python's stdlib ``difflib`` rather than a bespoke diff algorithm --
diffing text correctly is a solved problem, reinventing it would be
needless risk. What's here is a thin, genuinely useful wrapper around
it: a similarity ratio between two versions of a paragraph's text
(with HTML tags stripped first, so markup noise doesn't dominate the
comparison), used to flag trivial edits in a revision history UI. The
wrapper itself -- HTML stripping, the trivial-edit threshold -- is
simple enough to get subtly wrong and is what's actually tested here;
``difflib.SequenceMatcher`` doesn't need re-testing.
"""

from __future__ import annotations

import difflib
import re

_TAG_RE = re.compile(r'<[^>]+>')


def strip_html(text):
    return _TAG_RE.sub(' ', text or '')


def similarity_ratio(old_text, new_text):
    """0.0..1.0 -- how similar two versions of a paragraph's text are,
    via difflib's SequenceMatcher on the HTML-stripped text. 1.0 means
    identical (after stripping tags)."""
    return difflib.SequenceMatcher(
        None, strip_html(old_text), strip_html(new_text)).ratio()


def is_trivial_edit(old_text, new_text, threshold=0.98):
    """True if a revision barely changed the text (e.g. a typo fix) --
    lets a history view de-emphasize trivial entries instead of
    treating every edit as equally significant."""
    if old_text == new_text:
        return True
    return similarity_ratio(old_text, new_text) >= threshold
