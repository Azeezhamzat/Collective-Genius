"""Pluggable summarization backends.

The extractive backend (``engine.summarize``) is dependency-free and
always available -- it's the default, and the guaranteed fallback. This
module adds an optional LLM-backed backend behind the exact same
(comments, top_n, min_significant_words) -> [ScoredComment] shape,
selected via the ``A4_SUMMARIZATION_BACKEND`` setting (``'extractive'``
by default; set it to ``'llm'`` to opt in).

Any LLM backend failure -- no API key configured, the ``anthropic``
package not installed, a network error, a malformed response -- falls
back to the extractive backend via ``engine.summarize_with_fallback``
rather than breaking the page: summarization is a nice-to-have, never
something a discussion page should 500 over.

Not unit tested in this repo: unlike engine.py, this module needs
Django's settings machinery to even import, so it can't run standalone
the way the engine tests do, and the LLM path additionally needs a real
network call and API key that this environment doesn't have. Review it
carefully; the interesting, testable part -- the fallback-on-failure
wiring itself -- lives in ``engine.summarize_with_fallback`` and *is*
covered by ``tests/test_engine.py``.
"""

import json
import logging

from django.conf import settings

from . import engine

logger = logging.getLogger(__name__)


def extractive_backend(comments, top_n=5, min_significant_words=3):
    return engine.summarize(
        comments, top_n=top_n, min_significant_words=min_significant_words)


def llm_backend(comments, top_n=5, min_significant_words=3):
    """Ask an LLM to pick the ``top_n`` most representative comments.

    Requires the ``anthropic`` package (``pip install anthropic``,
    deliberately *not* added to requirements.txt since it's only needed
    by projects that opt into this backend) and ``ANTHROPIC_API_KEY``
    to be set in the environment. Raises on any failure; callers should
    use ``engine.summarize_with_fallback`` (see ``summarize()`` below)
    rather than calling this directly.
    """
    import anthropic  # optional dependency, only needed for this backend

    candidates = [
        (cid, text) for cid, text in comments
        if len(text.split()) >= min_significant_words
    ]
    if not candidates:
        return []

    numbered = '\n'.join(
        '{}. {}'.format(i, text) for i, (_cid, text) in enumerate(candidates)
    )
    prompt = (
        "Below is a numbered list of comments from a group discussion. "
        "Pick the {n} comments that best represent the discussion's "
        "actual central themes -- the ones a newcomer should read first "
        "to understand what the group is talking about. Reply with "
        "ONLY a JSON array of the chosen numbers, most representative "
        "first, e.g. [3, 1, 7]. No other text.\n\n{comments}"
    ).format(n=top_n, comments=numbered)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=getattr(settings, 'A4_SUMMARIZATION_LLM_MODEL',
                      'claude-sonnet-5'),
        max_tokens=256,
        messages=[{'role': 'user', 'content': prompt}],
    )
    indices = json.loads(response.content[0].text.strip())
    if not isinstance(indices, list):
        raise ValueError(
            'expected a JSON array of indices, got: {!r}'.format(indices))

    results = []
    for rank, index in enumerate(indices[:top_n]):
        if not isinstance(index, int) or not (0 <= index < len(candidates)):
            continue
        comment_id, text = candidates[index]
        # Rank is strictly increasing across the model's own ordering,
        # so this score keeps that order intact through any downstream
        # sort-by-score -- it isn't meant to be compared across runs.
        score = 1.0 - (rank / max(top_n, 1))
        results.append(engine.ScoredComment(
            comment_id=comment_id, score=score,
            n_significant_words=len(text.split())))
    return results


BACKENDS = {
    'extractive': extractive_backend,
    'llm': llm_backend,
}


def _log_fallback(err):
    logger.warning(
        'Summarization backend failed, falling back to extractive: %s',
        err, exc_info=err)


def summarize(comments, top_n=5, min_significant_words=3):
    """Summarize using the backend named by
    ``settings.A4_SUMMARIZATION_BACKEND`` (default ``'extractive'``),
    falling back to the extractive backend on any failure or if an
    unknown backend name is configured.
    """
    backend_name = getattr(settings, 'A4_SUMMARIZATION_BACKEND',
                           'extractive')
    backend = BACKENDS.get(backend_name, extractive_backend)

    if backend is extractive_backend:
        return extractive_backend(
            comments, top_n=top_n,
            min_significant_words=min_significant_words)

    return engine.summarize_with_fallback(
        backend, extractive_backend, comments, top_n=top_n,
        min_significant_words=min_significant_words,
        on_fallback=_log_fallback,
    )
