"""Unit tests for the pure-Python TF-IDF/cosine-similarity engine.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.deduplication import engine


class CosineSimilarityTests(unittest.TestCase):

    def test_identical_vectors_score_one(self):
        vec = {'bike': 0.5, 'lane': 0.3}
        self.assertAlmostEqual(engine.cosine_similarity(vec, vec), 1.0)

    def test_disjoint_vectors_score_zero(self):
        self.assertEqual(
            engine.cosine_similarity({'bike': 1.0}, {'dog': 1.0}), 0.0)

    def test_empty_vector_scores_zero(self):
        self.assertEqual(engine.cosine_similarity({}, {'bike': 1.0}), 0.0)
        self.assertEqual(engine.cosine_similarity({'bike': 1.0}, {}), 0.0)


class FindSimilarTests(unittest.TestCase):

    def setUp(self):
        self.corpus = [
            ('1', 'Build a protected bike lane on Main Street downtown'),
            ('2', 'Add a protected bike lane along Main Street downtown'),
            ('3', 'We should build a new dog park in the north district'),
            ('4', 'More funding for the downtown library renovation'),
        ]

    def test_near_duplicate_wording_scores_highest(self):
        results = engine.find_similar(
            'Please build a protected bike lane on Main Street downtown',
            self.corpus, top_n=4, min_score=0.0)
        self.assertEqual(results[0].doc_id, '1')
        self.assertEqual(results[1].doc_id, '2')
        # the two near-duplicate bike-lane ideas should clearly outscore
        # the unrelated dog park and library proposals
        self.assertGreater(results[0].score, results[2].score)
        self.assertGreater(results[1].score, results[3].score)

    def test_unrelated_query_returns_nothing_above_threshold(self):
        results = engine.find_similar(
            'We need better school lunch options',
            self.corpus, min_score=0.3)
        self.assertEqual(results, [])

    def test_empty_query_returns_empty(self):
        self.assertEqual(engine.find_similar('', self.corpus), [])

    def test_empty_corpus_returns_empty(self):
        self.assertEqual(engine.find_similar('bike lane', []), [])

    def test_top_n_limits_results(self):
        results = engine.find_similar(
            'downtown Main Street bike lane', self.corpus,
            top_n=1, min_score=0.0)
        self.assertEqual(len(results), 1)

    def test_min_score_filters_out_weak_matches(self):
        loose = engine.find_similar(
            'downtown', self.corpus, top_n=10, min_score=0.0)
        strict = engine.find_similar(
            'downtown', self.corpus, top_n=10, min_score=0.9)
        self.assertGreater(len(loose), len(strict))


if __name__ == '__main__':
    unittest.main()
