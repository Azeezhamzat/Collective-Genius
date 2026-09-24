"""Translation backends.

``settings.A4_TRANSLATION_BACKEND`` selects one:

* ``'none'`` (the default) -- translation is off. ``is_enabled()``
  returns False and callers should not offer a "Translate" control at
  all. This is the only backend that needs no extra dependency.
* ``'llm'`` -- translates via Claude (the ``anthropic`` package,
  deliberately not added to requirements.txt since it's optional; ``pip
  install anthropic`` plus ``ANTHROPIC_API_KEY`` to use it). Any failure
  (no key, package missing, network error) falls back to returning the
  original, untranslated text via ``engine.translate_with_fallback`` --
  a failed translation should never break the page, just fail to help.

Not unit tested in this repo, for the same reason as
apps/summarization/backends.py: it needs django.conf.settings just to
import, and Django isn't installed in this sandbox, let alone network
access for the real call. The tested part is the fallback wiring itself
(apps/translation/engine.py, apps/translation/tests/test_engine.py).
"""

import logging

from django.conf import settings

from . import engine

logger = logging.getLogger(__name__)


def is_enabled():
    return getattr(settings, 'A4_TRANSLATION_BACKEND', 'none') != 'none'


def _identity_backend(text, target_language):
    return text


def _llm_backend(text, target_language):
    import anthropic  # optional dependency, only needed for this backend

    language_names = dict(getattr(settings, 'LANGUAGES', ()))
    target_name = language_names.get(target_language, target_language)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=getattr(settings, 'A4_TRANSLATION_LLM_MODEL',
                      'claude-sonnet-5'),
        max_tokens=1024,
        messages=[{
            'role': 'user',
            'content': (
                'Translate the following text to {language}. Reply with '
                'ONLY the translation, no notes or explanation, no '
                'quotation marks.\n\n{text}'
            ).format(language=target_name, text=text),
        }],
    )
    translated = response.content[0].text.strip()
    if not translated:
        raise ValueError('empty translation returned')
    return translated


_BACKENDS = {
    'llm': _llm_backend,
}


def _log_fallback(err):
    logger.warning(
        'Translation backend failed, showing original text: %s',
        err, exc_info=err)


def translate(text, target_language):
    """Translate ``text`` to ``target_language`` using the configured
    backend, or return it unchanged if translation is off or fails.
    """
    if not is_enabled() or not text:
        return text

    backend_name = getattr(settings, 'A4_TRANSLATION_BACKEND', 'none')
    backend = _BACKENDS.get(backend_name)
    if backend is None:
        return text

    return engine.translate_with_fallback(
        backend, _identity_backend, text, target_language,
        on_fallback=_log_fallback,
    )
