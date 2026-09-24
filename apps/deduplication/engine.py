"""Pure-Python TF-IDF + cosine similarity, for finding ideas that look
like near-duplicates of each other by text alone.

Standard, well-understood technique (no ML library, no external corpus):
term frequency-inverse document frequency weights words that are
distinctive to a document over words that are common across the whole
corpus, then cosine similarity between two documents' weighted vectors
gives a 0..1-ish score for how similar their wording is. Good enough to
flag "someone already proposed almost exactly this" without needing a
network call or an API key.

No Django dependency, so this is unit tested standalone.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

_WORD_RE = re.compile(r"[A-Za-z']+")

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
    return [
        w for w in (m.lower() for m in _WORD_RE.findall(text or ''))
        if len(w) > 2 and w not in STOPWORDS
    ]


def _term_frequencies(tokens):
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = len(tokens)
    return {word: count / total for word, count in counts.items()}


def _inverse_document_frequencies(token_lists):
    token_lists = list(token_lists)
    n = len(token_lists)
    if n == 0:
        return {}
    document_frequency = Counter()
    for tokens in token_lists:
        document_frequency.update(set(tokens))
    return {
        word: math.log(n / (1 + count)) + 1
        for word, count in document_frequency.items()
    }


def _tfidf_vector(tokens, idf):
    tf = _term_frequencies(tokens)
    return {word: weight * idf.get(word, 0.0) for word, weight in tf.items()}


def cosine_similarity(vec_a, vec_b):
    if not vec_a or not vec_b:
        return 0.0
    common = set(vec_a) & set(vec_b)
    dot = sum(vec_a[w] * vec_b[w] for w in common)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class SimilarDocument:
    doc_id: str
    score: float


def find_similar(query_text, documents, top_n=5, min_score=0.15):
    """Rank ``documents`` by text similarity to ``query_text``.

    ``documents``: iterable of (doc_id, text) pairs -- the existing
    corpus to compare against (e.g. every idea already submitted in a
    module).

    Returns up to ``top_n`` SimilarDocument with score >= ``min_score``,
    highest first. Empty query or empty corpus returns [].
    """
    query_tokens = tokenize(query_text)
    if not query_tokens:
        return []

    doc_list = [(doc_id, tokenize(text)) for doc_id, text in documents]
    if not doc_list:
        return []

    idf = _inverse_document_frequencies(
        [tokens for _, tokens in doc_list] + [query_tokens])
    query_vec = _tfidf_vector(query_tokens, idf)

    results = []
    for doc_id, tokens in doc_list:
        if not tokens:
            continue
        score = cosine_similarity(query_vec, _tfidf_vector(tokens, idf))
        if score >= min_score:
            results.append(SimilarDocument(doc_id, score))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_n]
