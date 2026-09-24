"""Unit tests for the pure-Python argument-map tree builder.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.argumentmapping import engine


def nodes(rows):
    """rows: iterable of (id, parent_id, stance)."""
    return [engine.RawNode(i, p, s) for i, p, s in rows]


class BuildTreeTests(unittest.TestCase):

    def test_empty_input(self):
        self.assertEqual(engine.build_tree([]), [])

    def test_single_root_node(self):
        trees = engine.build_tree(nodes([('a', None, None)]))
        self.assertEqual(len(trees), 1)
        self.assertEqual(trees[0].id, 'a')
        self.assertEqual(trees[0].children, [])

    def test_nested_reply_chain(self):
        trees = engine.build_tree(nodes([
            ('a', None, engine.SUPPORTS),
            ('b', 'a', engine.OPPOSES),
            ('c', 'b', engine.SUPPORTS),
        ]))
        self.assertEqual(len(trees), 1)
        root = trees[0]
        self.assertEqual(root.id, 'a')
        self.assertEqual(len(root.children), 1)
        self.assertEqual(root.children[0].id, 'b')
        self.assertEqual(root.children[0].children[0].id, 'c')

    def test_multiple_roots(self):
        trees = engine.build_tree(nodes([
            ('a', None, None),
            ('b', None, None),
        ]))
        self.assertEqual({t.id for t in trees}, {'a', 'b'})

    def test_sibling_replies_both_attach_to_shared_parent(self):
        trees = engine.build_tree(nodes([
            ('a', None, None),
            ('b', 'a', engine.SUPPORTS),
            ('c', 'a', engine.OPPOSES),
        ]))
        root = trees[0]
        self.assertEqual({c.id for c in root.children}, {'b', 'c'})

    def test_dangling_parent_reference_becomes_a_root(self):
        # 'b' claims parent 'ghost', which doesn't exist in the input --
        # real comment data can't produce this, but the builder shouldn't
        # crash on it.
        trees = engine.build_tree(nodes([('b', 'ghost', None)]))
        self.assertEqual(len(trees), 1)
        self.assertEqual(trees[0].id, 'b')

    def test_pure_cycle_has_no_valid_root_and_is_dropped(self):
        # Malformed data: a claims parent b, b claims parent a. Since
        # every node's parent_id resolves to another real node, neither
        # qualifies as a root (parent_id=None or dangling) -- there is no
        # valid entry point into this cycle, so both nodes are correctly
        # left out rather than guessed at. The only hard requirement is
        # that this terminates instead of recursing forever.
        trees = engine.build_tree(nodes([
            ('a', 'b', None),
            ('b', 'a', None),
        ]))
        self.assertEqual(trees, [])

    def test_cycle_reachable_from_a_real_root_does_not_infinite_loop(self):
        # 'a' is a legitimate root; 'b' and 'c' form a cycle underneath
        # it. attach()'s `seen` guard must stop recursion at the second
        # visit to 'b' instead of looping forever.
        trees = engine.build_tree(nodes([
            ('a', None, None),
            ('b', 'a', None),
            ('c', 'b', None),
        ] + [('b', 'c', None)]))  # duplicate id 'b', now parented under c
        self.assertEqual(len(trees), 1)
        self.assertEqual(trees[0].id, 'a')


class BuildArgumentMapTests(unittest.TestCase):

    def test_counts_propagate_up_including_self(self):
        trees = engine.build_argument_map(nodes([
            ('a', None, engine.SUPPORTS),
            ('b', 'a', engine.SUPPORTS),
            ('c', 'a', engine.OPPOSES),
            ('d', 'b', engine.SUPPORTS),
        ]))
        root = trees[0]
        self.assertEqual(root.id, 'a')
        # a itself supports (+1), b supports (+1), d supports (+1), c opposes
        self.assertEqual(root.support_count, 3)
        self.assertEqual(root.oppose_count, 1)

    def test_unset_stance_does_not_count_either_way(self):
        trees = engine.build_argument_map(nodes([('a', None, None)]))
        self.assertEqual(trees[0].support_count, 0)
        self.assertEqual(trees[0].oppose_count, 0)

    def test_children_sorted_by_strength_descending(self):
        trees = engine.build_argument_map(nodes([
            ('root', None, None),
            ('weak_support', 'root', engine.SUPPORTS),
            ('strong_oppose', 'root', engine.OPPOSES),
            ('strong_support', 'root', engine.SUPPORTS),
            ('s2', 'strong_support', engine.SUPPORTS),
            ('s3', 'strong_support', engine.SUPPORTS),
        ]))
        root = trees[0]
        child_ids = [c.id for c in root.children]
        # strong_support has 3 supports net (+3), weak_support has 1 (+1),
        # strong_oppose has -1 -- so this exact order is required.
        self.assertEqual(
            child_ids, ['strong_support', 'weak_support', 'strong_oppose'])

    def test_roots_are_sorted_by_strength_too(self):
        trees = engine.build_argument_map(nodes([
            ('weak', None, engine.SUPPORTS),
            ('strong', None, engine.SUPPORTS),
            ('s_child', 'strong', engine.SUPPORTS),
        ]))
        self.assertEqual([t.id for t in trees], ['strong', 'weak'])


if __name__ == '__main__':
    unittest.main()
