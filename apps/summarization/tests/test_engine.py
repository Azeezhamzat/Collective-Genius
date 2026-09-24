"""Unit tests for the pure-Python extractive summarization engine.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.summarization import engine


class TokenizeTests(unittest.TestCase):

    def test_lowercases_and_strips_punctuation(self):
        self.assertEqual(
            engine.tokenize("Bikes, Bikes, and BIKES!"),
            ['bikes', 'bikes', 'bikes'])

    def test_drops_stopwords_and_short_words(self):
        tokens = engine.tokenize("this is a great idea for the city")
        self.assertNotIn('this', tokens)
        self.assertNotIn('is', tokens)
        self.assertNotIn('a', tokens)
        self.assertNotIn('for', tokens)
        self.assertNotIn('the', tokens)
        self.assertIn('great', tokens)
        self.assertIn('idea', tokens)
        self.assertIn('city', tokens)

    def test_empty_and_none_text(self):
        self.assertEqual(engine.tokenize(''), [])
        self.assertEqual(engine.tokenize(None), [])


class SummarizeTests(unittest.TestCase):

    def setUp(self):
        # Five comments clearly about "bike lanes downtown", plus one
        # off-topic tangent about "parking fees" that shares no
        # vocabulary with the rest.
        self.comments = [
            ('1', 'We need more protected bike lanes downtown'),
            ('2', 'Bike lanes downtown would make cycling much safer'),
            ('3', 'I support new bike lanes in the downtown area'),
            ('4', 'Protected bike lanes downtown are long overdue'),
            ('5', 'Parking fees at the garage are way too expensive'),
        ]

    def test_on_topic_comments_outscore_the_tangent(self):
        results = engine.summarize(self.comments, top_n=5)
        by_id = {r.comment_id: r.score for r in results}
        # every "bike lanes downtown" comment should outscore the one
        # comment that shares none of that shared vocabulary
        for cid in ('1', '2', '3', '4'):
            self.assertGreater(by_id[cid], by_id['5'], msg=cid)

    def test_top_n_limits_results(self):
        results = engine.summarize(self.comments, top_n=2)
        self.assertEqual(len(results), 2)

    def test_min_significant_words_excludes_short_comments(self):
        comments = self.comments + [('6', '+1')]
        results = engine.summarize(
            comments, top_n=10, min_significant_words=3)
        ids = {r.comment_id for r in results}
        self.assertNotIn('6', ids)

    def test_empty_input(self):
        self.assertEqual(engine.summarize([]), [])

    def test_single_comment(self):
        results = engine.summarize([('1', 'This is a fine short comment')])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].comment_id, '1')


class TopKeywordsTests(unittest.TestCase):

    def test_most_shared_words_ranked_first(self):
        comments = [
            ('1', 'bike lanes downtown'),
            ('2', 'bike lanes safer'),
            ('3', 'bike lanes overdue'),
            ('4', 'parking fees expensive'),
        ]
        keywords = engine.top_keywords(comments, top_n=3)
        words = [w for w, _count in keywords]
        self.assertIn('bike', words)
        self.assertIn('lanes', words)
        # 'bike' and 'lanes' each appear in 3 of 4 comments, more than
        # any word in the single unrelated comment.
        counts = dict(keywords)
        self.assertEqual(counts['bike'], 3)
        self.assertEqual(counts['lanes'], 3)

    def test_empty_input(self):
        self.assertEqual(engine.top_keywords([]), [])


if __name__ == '__main__':
    unittest.main()
