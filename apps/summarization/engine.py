"""Pure-Python extractive summarization for a discussion's comments.

Uses word-frequency centrality, a simplified version of Luhn's classic
1958 extractive-summarization method: a comment that uses vocabulary
shared with many other comments in the same discussion is more likely to
be about the discussion's actual central themes than a comment that's
off on its own tangent, so it scores higher and is more representative
to surface in a "key points" summary.

Deliberately does not call out to an LLM or any ML library: this keeps
the default summarizer dependency-free, deterministic, and unit
testable without network access or an API key. A caller that wants an
LLM-backed summary can swap in a different backend behind the same
``summarize(comments)`` signature -- nothing here assumes this
particular implementation.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

_WORD_RE = re.compile(r"[A-Za-z']+")

# A short, deliberately generic English stopword list -- not a full NLP
# stopword corpus, just enough to keep "the", "and", "this" etc. from
# dominating word-frequency scoring.
STOPWORDS = frozenset("""
a about above after again against all am an and any are aren't as at be
because been before being below between both but by can't cannot could
couldn't did didn't do does doesn't doing don't down during each few for
from further had hadn't has hasn't have haven't having he he'd he'll
he's her here here's hers herself him himself his how how's i i'd i'll
i'm i've if in into is isn't it it's its itself let's me more most
mustn't my myself no nor not of off on once only or other ought our
ours ourselves out over own same shan't she she'd she'll she's should
shouldn't so some such than that that's the their theirs them
themselves then there there's these they they'd they'll they're they've
this those through to too under until up very was wasn't we we'd we'll
we're we've were weren't what what's when when's where where's which
while who who's whom why why's with won't would wouldn't you you'd
you'll you're you've your yours yourself yourselves
""".split())


def tokenize(text):
    """Significant (non-stopword, len > 2) lowercase words in ``text``."""
    return [
        w for w in (m.lower() for m in _WORD_RE.findall(text or ''))
        if len(w) > 2 and w not in STOPWORDS
    ]


def word_frequencies(token_lists):
    """Counter of word -> number of *documents* containing it (each
    document counted once per word, however often it repeats within
    that one document) -- this stops one repetitive comment from
    dominating the frequency counts on its own.
    """
    freq = Counter()
    for tokens in token_lists:
        freq.update(set(tokens))
    return freq


def _score(tokens, freq):
    unique = set(tokens)
    if not unique:
        return 0.0
    return sum(freq[w] for w in unique) / len(unique)


@dataclass
class ScoredComment:
    comment_id: str
    score: float
    n_significant_words: int


def summarize(comments, top_n=5, min_significant_words=3):
    """Pick the ``top_n`` most representative comments.

    ``comments``: iterable of (comment_id, text) pairs.
    Comments with fewer than ``min_significant_words`` non-stopword
    words are excluded -- too short to meaningfully score, and usually
    not worth surfacing as a "key point" anyway (e.g. "+1", "agreed").
    Returns a list of ScoredComment, highest score first; ties keep the
    original input order (stable sort).
    """
    tokenized = [(cid, tokenize(text)) for cid, text in comments]
    freq = word_frequencies(tokens for _, tokens in tokenized)

    scored = [
        ScoredComment(cid, _score(tokens, freq), len(tokens))
        for cid, tokens in tokenized
        if len(tokens) >= min_significant_words
    ]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored[:top_n]


def top_keywords(comments, top_n=10):
    """The ``top_n`` most-shared significant words across ``comments``
    -- a quick "what is this discussion about" list. Same (comment_id,
    text) input shape as ``summarize``.
    """
    token_lists = [tokenize(text) for _, text in comments]
    freq = word_frequencies(token_lists)
    return freq.most_common(top_n)
