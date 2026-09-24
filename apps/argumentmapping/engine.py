"""Pure-Python argument-map tree builder.

Threaded comments already form a tree (each reply's parent is either the
thing being discussed or another comment). This module takes that tree,
plus an optional support/oppose stance on each comment, and produces a
Kialo-style structure: every node knows how many supporting versus
opposing statements exist in its own subtree, so a view can sort each
branch by strength and show at a glance where the weight of an argument
actually is -- not just how many replies it has.

No Django dependency, so the tree-building and scoring logic is unit
tested standalone (see tests/test_engine.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

SUPPORTS = 'supports'
OPPOSES = 'opposes'


@dataclass(frozen=True)
class RawNode:
    id: str
    parent_id: str | None  # None = attaches directly to the debated subject
    stance: str | None = None  # SUPPORTS, OPPOSES, or None (no stance set)


@dataclass
class ArgumentNode:
    id: str
    stance: str | None
    children: list = field(default_factory=list)
    support_count: int = 0  # this node + all descendants
    oppose_count: int = 0


def build_tree(nodes):
    """Turn a flat list of RawNode into a forest of ArgumentNode trees.

    A node whose parent_id doesn't match any other node's id (including
    None, or a dangling reference) becomes a root -- this can't happen
    for real comment data, since it always ultimately traces back to the
    thing being discussed, but keeping it tolerant here means a caller
    with slightly stale data degrades gracefully instead of crashing.
    """
    by_id = {n.id: ArgumentNode(id=n.id, stance=n.stance) for n in nodes}

    children_of = {}
    roots = []
    for n in nodes:
        if n.parent_id is not None and n.parent_id in by_id:
            children_of.setdefault(n.parent_id, []).append(n.id)
        else:
            roots.append(n.id)

    def attach(node_id, seen):
        # seen guards against a cyclic parent chain in bad data; without
        # it a cycle would recurse forever.
        node = by_id[node_id]
        for child_id in children_of.get(node_id, []):
            if child_id in seen:
                continue
            node.children.append(attach(child_id, seen | {child_id}))
        return node

    return [attach(root_id, {root_id}) for root_id in roots]


def _compute_counts(node):
    support = 1 if node.stance == SUPPORTS else 0
    oppose = 1 if node.stance == OPPOSES else 0
    for child in node.children:
        _compute_counts(child)
        support += child.support_count
        oppose += child.oppose_count
    node.support_count = support
    node.oppose_count = oppose


def _sort_by_strength(node):
    node.children.sort(
        key=lambda c: (c.support_count - c.oppose_count, c.support_count),
        reverse=True,
    )
    for child in node.children:
        _sort_by_strength(child)


def build_argument_map(nodes):
    """Build the full, scored, sorted forest for a discussion.

    Combines build_tree + count propagation + strength sorting -- the
    single entry point callers should use.
    """
    trees = build_tree(nodes)
    for tree in trees:
        _compute_counts(tree)
        _sort_by_strength(tree)
    # Sort the roots themselves by strength too.
    trees.sort(key=lambda t: (t.support_count - t.oppose_count,
                              t.support_count), reverse=True)
    return trees
