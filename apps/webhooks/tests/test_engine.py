"""Unit tests for the pure-Python webhook signing and retry-scheduling
core.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.webhooks import engine


class CanonicalPayloadTests(unittest.TestCase):

    def test_deterministic_regardless_of_dict_key_order(self):
        a = engine.canonical_payload('thing.happened', {'b': 2, 'a': 1})
        b = engine.canonical_payload('thing.happened', {'a': 1, 'b': 2})
        self.assertEqual(a, b)

    def test_different_data_produces_different_payload(self):
        a = engine.canonical_payload('thing.happened', {'id': 1})
        b = engine.canonical_payload('thing.happened', {'id': 2})
        self.assertNotEqual(a, b)


class SignVerifyTests(unittest.TestCase):

    def test_correct_signature_verifies(self):
        payload = engine.canonical_payload('thing.happened', {'id': 1})
        signature = engine.sign(payload, 'my-secret')
        self.assertTrue(engine.verify(payload, 'my-secret', signature))

    def test_wrong_secret_fails_verification(self):
        payload = engine.canonical_payload('thing.happened', {'id': 1})
        signature = engine.sign(payload, 'my-secret')
        self.assertFalse(
            engine.verify(payload, 'a-different-secret', signature))

    def test_tampered_payload_fails_verification(self):
        payload = engine.canonical_payload('thing.happened', {'id': 1})
        signature = engine.sign(payload, 'my-secret')
        tampered = engine.canonical_payload('thing.happened', {'id': 2})
        self.assertFalse(engine.verify(tampered, 'my-secret', signature))

    def test_tampered_signature_fails_verification(self):
        payload = engine.canonical_payload('thing.happened', {'id': 1})
        signature = engine.sign(payload, 'my-secret')
        flipped = ('0' if signature[0] != '0' else '1') + signature[1:]
        self.assertFalse(engine.verify(payload, 'my-secret', flipped))

    def test_signature_is_deterministic(self):
        payload = engine.canonical_payload('thing.happened', {'id': 1})
        self.assertEqual(
            engine.sign(payload, 'my-secret'),
            engine.sign(payload, 'my-secret'))


class RetryScheduleTests(unittest.TestCase):

    def test_first_attempt_failing_should_retry(self):
        self.assertTrue(engine.should_retry(1))

    def test_retries_are_exhausted_eventually(self):
        last_attempt = len(engine.RETRY_SCHEDULE_SECONDS)
        self.assertTrue(engine.should_retry(last_attempt))
        self.assertFalse(engine.should_retry(last_attempt + 1))

    def test_delays_increase(self):
        delays = [
            engine.retry_delay_seconds(n)
            for n in range(1, len(engine.RETRY_SCHEDULE_SECONDS) + 1)
        ]
        self.assertEqual(delays, sorted(delays))
        self.assertLess(delays[0], delays[-1])

    def test_retry_delay_raises_once_schedule_exhausted(self):
        last_attempt = len(engine.RETRY_SCHEDULE_SECONDS)
        with self.assertRaises(IndexError):
            engine.retry_delay_seconds(last_attempt + 1)


if __name__ == '__main__':
    unittest.main()
