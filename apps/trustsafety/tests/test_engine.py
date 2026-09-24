"""Unit tests for the pure-Python rate-limiting and spam-scoring core.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.trustsafety import engine


class TokenBucketTests(unittest.TestCase):

    def test_new_bucket_starts_full(self):
        bucket = engine.new_bucket(capacity=5, refill_rate=1, now=0.0)
        self.assertEqual(bucket.tokens, 5)

    def test_consuming_within_capacity_succeeds(self):
        bucket = engine.new_bucket(capacity=5, refill_rate=1, now=0.0)
        for _ in range(5):
            self.assertTrue(bucket.consume(now=0.0))
        self.assertEqual(bucket.tokens, 0)

    def test_exceeding_capacity_is_rejected(self):
        bucket = engine.new_bucket(capacity=5, refill_rate=1, now=0.0)
        for _ in range(5):
            bucket.consume(now=0.0)
        self.assertFalse(bucket.consume(now=0.0))

    def test_rejected_consume_does_not_deduct_tokens(self):
        bucket = engine.new_bucket(capacity=1, refill_rate=0, now=0.0)
        bucket.consume(now=0.0)  # uses the only token
        self.assertFalse(bucket.consume(now=0.0, amount=1))
        self.assertEqual(bucket.tokens, 0)

    def test_refills_over_time(self):
        bucket = engine.new_bucket(capacity=5, refill_rate=1, now=0.0)
        for _ in range(5):
            bucket.consume(now=0.0)
        self.assertFalse(bucket.consume(now=0.5))
        self.assertTrue(bucket.consume(now=1.0))  # 1 second * 1/sec = 1 token

    def test_refill_is_capped_at_capacity(self):
        bucket = engine.new_bucket(capacity=5, refill_rate=1, now=0.0)
        bucket.consume(now=0.0)
        bucket._refill(now=1000.0)  # huge elapsed time
        self.assertEqual(bucket.tokens, 5)

    def test_can_consume_more_than_one_token_at_once(self):
        bucket = engine.new_bucket(capacity=5, refill_rate=1, now=0.0)
        self.assertTrue(bucket.consume(now=0.0, amount=3))
        self.assertEqual(bucket.tokens, 2)
        self.assertFalse(bucket.consume(now=0.0, amount=3))


class ScoreTextTests(unittest.TestCase):

    def test_normal_message_scores_low(self):
        result = engine.score_text(
            'I think we should extend the deadline by a week so more '
            'people can weigh in before the vote closes.')
        self.assertLess(result.score, 0.3)

    def test_empty_text_does_not_crash(self):
        result = engine.score_text('')
        self.assertEqual(result.score, 0.0)
        result = engine.score_text(None)
        self.assertEqual(result.score, 0.0)

    def test_link_dominated_short_message_scores_high(self):
        result = engine.score_text('check this out http://spam.example/x')
        self.assertGreaterEqual(result.score, 0.5)
        self.assertIn('very short message dominated by a link',
                      result.reasons)

    def test_many_links_scores_high(self):
        text = ('http://a.example http://b.example http://c.example '
               'http://d.example http://e.example')
        result = engine.score_text(text)
        self.assertGreaterEqual(result.score, 0.5)

    def test_repeated_characters_contribute(self):
        result = engine.score_text('this is amaaaaazing buy now')
        self.assertIn('repeated characters', result.reasons)

    def test_excessive_capitalization_contributes(self):
        result = engine.score_text(
            'THIS IS A HUGE OPPORTUNITY YOU CANNOT MISS OUT ON TODAY')
        self.assertIn('excessive capitalization', result.reasons)

    def test_score_never_exceeds_one(self):
        text = ('http://a.example http://b.example http://c.example '
               'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        result = engine.score_text(text)
        self.assertLessEqual(result.score, 1.0)


class IsLikelySpamTests(unittest.TestCase):

    def test_default_threshold(self):
        self.assertFalse(engine.is_likely_spam('a normal comment'))
        self.assertTrue(engine.is_likely_spam(
            'click here http://spam.example/x'))

    def test_custom_threshold(self):
        # five repeated 'a's triggers only the repeated-characters rule
        # (+0.2) -- enough to clear a low threshold, not a high one.
        mild = 'this is amaaaaazing'
        self.assertFalse(engine.is_likely_spam(mild, threshold=0.9))
        self.assertTrue(engine.is_likely_spam(mild, threshold=0.1))


if __name__ == '__main__':
    unittest.main()
