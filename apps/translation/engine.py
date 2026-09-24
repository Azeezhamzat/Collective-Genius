"""Pure-Python helpers for on-demand machine translation of discussion
content (comments), so a group that isn't all working in the
platform's maintained UI languages (currently English and German; see
LANGUAGES in settings) isn't stuck reading a discussion it can't follow.

This is deliberately separate from -- and doesn't touch -- Django's own
gettext-based UI translation machinery, which this project already has
a real workflow for (transifex-client, in requirements/dev.txt). That
system translates interface chrome ("Submit", "Comments", ...) from
maintained .po files. This module translates user-generated *content*
(what people actually wrote) on demand, via an optional backend, since
there's no .po file for "what a participant typed into a comment box."

No Django dependency here: the actual network-calling backend lives in
``backends.py`` (which does need Django, to read its settings, and so
isn't unit tested the way this is -- see the module docstring there for
why). What's here is the same "try the real thing, degrade safely"
wiring apps/summarization/engine.py uses, applied to translation.
"""

from __future__ import annotations


def translate_with_fallback(primary, fallback, text, target_language,
                            on_fallback=None):
    """Call ``primary(text, target_language)``; if it raises *any*
    exception, call ``fallback(text, target_language)`` instead and
    return that.

    A failed translation should show the original text (plus, ideally,
    a "translation unavailable" note from the caller), never break the
    page. ``on_fallback``, if given, is called with the caught
    exception before returning the fallback result, so callers can log
    without this function needing to know about logging configuration.
    """
    try:
        return primary(text, target_language)
    except Exception as err:  # noqa: BLE001 - deliberately broad: any
        # failure of an optional backend should degrade, not propagate.
        if on_fallback is not None:
            on_fallback(err)
        return fallback(text, target_language)
