"""The immutable ``outputs/raw`` guard for parity generator destinations.

Split out of ``parity_contract`` by responsibility; ``raw_tree_destination_error``
is re-exported from there for the family CLIs, which refuse to generate a batch
beneath the immutable corpus before writing anything.
"""

from __future__ import annotations

from pathlib import Path


def _points_under_raw_tree(candidate):
    """True when consecutive path parts spell an ``outputs/raw`` tree."""
    parts = candidate.parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def raw_tree_destination_error(destination):
    """Message when ``destination`` points beneath an ``outputs/raw`` tree.

    ``outputs/raw/`` is the immutable corpus: generated rounds reach it only
    through the transaction/publish path, never directly from a generator
    CLI. Both the lexical argument and its resolved form are checked, so
    neither a ``..`` respelling nor a symlink detour can land a fresh batch
    inside a raw tree. Returns ``None`` for an acceptable destination.
    """
    destination = Path(destination)
    for candidate in (destination, destination.resolve(strict=False)):
        if _points_under_raw_tree(candidate):
            return (
                "refusing to generate beneath immutable outputs/raw: "
                f"{destination}"
            )
    return None
