"""Unit tests for the pure-Python paragraph-revision diff helpers.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.documentrevisions import engine


class StripHtmlTests(unittest.TestCase):

    def test_removes_tags(self):
        self.assertEqual(
            engine.strip_html('<p>Hello <b>world</b></p>'),
            ' Hello  world  ')

    def test_none_and_empty(self):
        self.assertEqual(engine.strip_html(None), '')
        self.assertEqual(engine.strip_html(''), '')


class SimilarityRatioTests(unittest.TestCase):

    def test_identical_text_scores_one(self):
        self.assertEqual(
            engine.similarity_ratio('same text', 'same text'), 1.0)

    def test_identical_after_stripping_markup_scores_one(self):
        self.assertEqual(
            engine.similarity_ratio(
                '<p>same text</p>', '<div>same text</div>'), 1.0)

    def test_completely_different_text_scores_low(self):
        ratio = engine.similarity_ratio(
            'the quick brown fox', 'lorem ipsum dolor sit amet')
        self.assertLess(ratio, 0.3)

    def test_small_edit_scores_high(self):
        ratio = engine.similarity_ratio(
            'The proposal is due by Friday.',
            'The proposal is due by Monday.')
        self.assertGreaterEqual(ratio, 0.9)


class IsTrivialEditTests(unittest.TestCase):

    def test_identical_text_is_trivial(self):
        self.assertTrue(engine.is_trivial_edit('text', 'text'))

    def test_typo_fix_is_trivial(self):
        self.assertTrue(engine.is_trivial_edit(
            'The proposl is due Friday.',
            'The proposal is due Friday.'))

    def test_rewrite_is_not_trivial(self):
        self.assertFalse(engine.is_trivial_edit(
            'We should build a bike lane on Main Street.',
            'The budget for this quarter needs to be revised downward.'))

    def test_custom_threshold(self):
        old = 'one two three four five'
        new = 'one two three four SIX'
        # A near-total-word-match differs by one word: high ratio, but
        # not identical -- a strict enough threshold should reject it.
        self.assertTrue(engine.is_trivial_edit(old, new, threshold=0.5))
        self.assertFalse(engine.is_trivial_edit(old, new, threshold=0.999))


if __name__ == '__main__':
    unittest.main()
