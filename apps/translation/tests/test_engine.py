"""Unit tests for the pure-Python translate-with-fallback wiring.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.translation import engine


class TranslateWithFallbackTests(unittest.TestCase):

    def test_returns_primary_result_when_primary_succeeds(self):
        primary = lambda text, target_language: 'translated: ' + text
        fallback = lambda text, target_language: text
        result = engine.translate_with_fallback(
            primary, fallback, 'hello', 'de')
        self.assertEqual(result, 'translated: hello')

    def test_falls_back_to_original_text_when_primary_raises(self):
        def primary(text, target_language):
            raise RuntimeError('backend unavailable')
        fallback = lambda text, target_language: text
        result = engine.translate_with_fallback(
            primary, fallback, 'hello', 'de')
        self.assertEqual(result, 'hello')

    def test_falls_back_on_any_exception_type(self):
        for exc_type in (ValueError, KeyError, ImportError, TypeError):
            def primary(text, target_language, _exc=exc_type):
                raise _exc('boom')
            fallback = lambda text, target_language: 'safe'
            result = engine.translate_with_fallback(
                primary, fallback, 'hello', 'de')
            self.assertEqual(result, 'safe', msg=exc_type)

    def test_on_fallback_callback_receives_the_exception(self):
        caught = []

        def primary(text, target_language):
            raise RuntimeError('boom')

        fallback = lambda text, target_language: text
        engine.translate_with_fallback(
            primary, fallback, 'hello', 'de', on_fallback=caught.append)

        self.assertEqual(len(caught), 1)
        self.assertIsInstance(caught[0], RuntimeError)

    def test_arguments_are_forwarded(self):
        seen = {}

        def primary(text, target_language):
            seen['args'] = (text, target_language)
            return 'ok'

        fallback = lambda text, target_language: None
        engine.translate_with_fallback(primary, fallback, 'hi there', 'fr')

        self.assertEqual(seen['args'], ('hi there', 'fr'))


if __name__ == '__main__':
    unittest.main()
