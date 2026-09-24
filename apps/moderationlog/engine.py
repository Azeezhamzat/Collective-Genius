"""Pure-Python diffing for comment moderation flags.

adhocracy4's Comment model represents every moderation action as one of
three independent boolean flags (``is_censored``, ``is_removed``,
``is_blocked``) rather than a single audit-log entry, so turning "a
comment was saved" into "here is what a moderator actually did" means
comparing the flags before and after a save and reporting exactly which
ones changed and in which direction. Getting that comparison right --
not double-counting an unrelated field change as a moderation action,
not missing a flag that flipped alongside another one -- is worth
testing directly.
"""

from __future__ import annotations

from dataclasses import dataclass

FLAGS = ('is_censored', 'is_removed', 'is_blocked')

SET = 'set'
CLEARED = 'cleared'


@dataclass(frozen=True)
class FlagChange:
    flag: str
    action: str  # SET or CLEARED


def diff_moderation_flags(old, new):
    """``old``/``new``: dict-like objects with (at least) the keys in
    ``FLAGS``, each a bool. Returns a list of FlagChange for every flag
    that differs between the two -- empty if nothing moderation-related
    changed. Extra keys in either dict are ignored.
    """
    changes = []
    for flag in FLAGS:
        old_value = bool(old.get(flag, False))
        new_value = bool(new.get(flag, False))
        if old_value != new_value:
            changes.append(FlagChange(flag, SET if new_value else CLEARED))
    return changes
