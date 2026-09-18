"""The immutable ``outputs/raw`` guard for parity generator destinations.

Split out of ``parity_contract`` by responsibility; ``raw_tree_destination_error``
is re-exported from there for the family CLIs, which refuse to generate a batch
beneath the immutable corpus before writing anything.
"""

from __future__ import annotations

from .import_twins import bind_import_twin

from pathlib import Path

try:
    from pipelines.raw_tree_guard import contains_raw_segments, is_under_raw
except ImportError:
    from raw_tree_guard import contains_raw_segments, is_under_raw


def _points_under_raw_tree(candidate):
    """True when consecutive path parts spell an ``outputs/raw`` tree."""
    return contains_raw_segments(candidate.parts)


def raw_tree_destination_error(destination):
    """Message when ``destination`` points beneath an ``outputs/raw`` tree.

    ``outputs/raw/`` is the immutable corpus: generated rounds reach it only
    through the transaction/publish path, never directly from a generator
    CLI. Both the lexical argument and its resolved form are checked, so
    neither a ``..`` respelling nor a symlink detour can land a fresh batch
    inside a raw tree. The shared guard also checks inode and bind-mount
    aliases. Returns ``None`` for an acceptable destination.
    """
    destination = Path(destination)
    if _points_under_raw_tree(destination) or is_under_raw(destination):
        return (
            "refusing to generate beneath immutable outputs/raw: "
            f"{destination}"
        )
    return None


bind_import_twin(__name__)
