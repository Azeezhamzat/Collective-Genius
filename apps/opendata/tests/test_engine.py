import unittest

from apps.opendata import engine


class CanonicalJsonTests(unittest.TestCase):

    def test_key_order_does_not_affect_output(self):
        a = engine.canonical_json({'b': 1, 'a': 2})
        b = engine.canonical_json({'a': 2, 'b': 1})
        self.assertEqual(a, b)

    def test_different_data_produces_different_output(self):
        a = engine.canonical_json({'a': 1})
        b = engine.canonical_json({'a': 2})
        self.assertNotEqual(a, b)


class ChecksumTests(unittest.TestCase):

    def test_deterministic(self):
        data = {'items': [{'id': 1, 'name': 'Idea'}]}
        self.assertEqual(engine.checksum(data), engine.checksum(data))

    def test_insertion_order_does_not_change_checksum(self):
        a = {'items': [{'id': 1, 'name': 'Idea'}], 'comments': []}
        b = {'comments': [], 'items': [{'name': 'Idea', 'id': 1}]}
        self.assertEqual(engine.checksum(a), engine.checksum(b))

    def test_changed_data_changes_checksum(self):
        a = {'items': [{'id': 1, 'name': 'Idea'}]}
        b = {'items': [{'id': 1, 'name': 'Idea, edited'}]}
        self.assertNotEqual(engine.checksum(a), engine.checksum(b))

    def test_has_sha256_prefix(self):
        self.assertTrue(engine.checksum({}).startswith('sha256:'))


class BuildDatasetTests(unittest.TestCase):

    def test_includes_schema_version(self):
        dataset = engine.build_dataset('my-project', '2026-01-01T00:00:00Z',
                                       {'items': []})
        self.assertEqual(dataset['schema_version'], engine.SCHEMA_VERSION)

    def test_includes_project_and_timestamp(self):
        dataset = engine.build_dataset('my-project', '2026-01-01T00:00:00Z',
                                       {'items': []})
        self.assertEqual(dataset['project'], 'my-project')
        self.assertEqual(dataset['generated_at'], '2026-01-01T00:00:00Z')

    def test_sections_carry_their_own_count(self):
        rows = [{'id': 1}, {'id': 2}]
        dataset = engine.build_dataset('p', 'now', {'items': rows})
        self.assertEqual(dataset['sections']['items']['count'], 2)
        self.assertEqual(dataset['sections']['items']['items'], rows)

    def test_checksum_matches_sections_checksum(self):
        sections = {'items': [{'id': 1}]}
        dataset = engine.build_dataset('p', 'now', sections)
        self.assertEqual(dataset['checksum'], engine.checksum(sections))

    def test_empty_sections_still_produces_valid_envelope(self):
        dataset = engine.build_dataset('p', 'now', {})
        self.assertEqual(dataset['sections'], {})
        self.assertIn('checksum', dataset)


if __name__ == '__main__':
    unittest.main()
