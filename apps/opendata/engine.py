"""Pure-Python core for the public, versioned project data export.

The "versioned" part of "open data & auditability" doesn't mean
semantic version numbers on the *content* -- a project's data changes
continuously as people participate, so there is no meaningful "v1.2" of
it. What actually matters to someone consuming this export (a
researcher, a journalist, a civic-tech tool) is:

* ``schema_version`` -- the *shape* of this JSON document. Bumped only
  when a field is renamed, removed, or reinterpreted; additive changes
  (a new optional field) don't need a bump. Lets a consumer's parser
  fail loudly instead of silently misreading a changed field.
* ``generated_at`` -- when this snapshot was produced.
* ``checksum`` -- a hash over the actual data, so two exports pulled at
  different times can be compared for "did anything change" without
  diffing the whole payload, and so a consumer can verify a copy of the
  export wasn't corrupted or tampered with in transit.

This module only builds and hashes that envelope from data it's given;
it has no knowledge of Projects, Comments, or Django at all, which is
what makes it testable without a database.
"""

from __future__ import annotations

import hashlib
import json

SCHEMA_VERSION = 1


def canonical_json(data):
    """A deterministic JSON encoding of ``data``: sorted keys, no
    incidental whitespace. Two calls with equivalent data (regardless
    of dict insertion order) always produce the same string -- required
    for the checksum below to mean anything.
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':'),
                      default=str)


def checksum(data):
    """A ``sha256:<hex>`` digest of ``data``'s canonical encoding."""
    digest = hashlib.sha256(canonical_json(data).encode('utf-8')).hexdigest()
    return 'sha256:{}'.format(digest)


def build_dataset(project_slug, generated_at, sections):
    """Build the full versioned export envelope.

    ``sections`` is a dict of section name -> list of plain dicts (e.g.
    ``{'items': [...], 'comments': [...], 'ratings': [...]}``). The
    checksum covers exactly this dict, so any change to any section
    changes the checksum.
    """
    return {
        'schema_version': SCHEMA_VERSION,
        'project': project_slug,
        'generated_at': generated_at,
        'checksum': checksum(sections),
        'sections': {
            name: {'count': len(rows), 'items': rows}
            for name, rows in sections.items()
        },
    }
