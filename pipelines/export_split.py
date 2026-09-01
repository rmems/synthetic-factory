#!/usr/bin/env python3
"""Deterministic train/eval split for one immutable curated snapshot.

Split out of ``export_hf.py`` by responsibility. Every decision ties back to
one salted hash bucket per row plus one deterministic ordering, with a
two-sided fallback that keeps both split sides nonempty.
"""

from __future__ import annotations

import hashlib
import sys
from typing import Sequence

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("export_split", allow_initializing=True):
        import export_split as _direct_export_split

        _require_local_sibling(_direct_export_split, "export_split")
        del _direct_export_split
    from .export_contract import ExportError, ViewerRow
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_split"
    )
    from export_contract import ExportError, ViewerRow


def split_bucket(row: ViewerRow, salt: str) -> float:
    """Map a row to a stable [0,1) bucket that does not depend on ordering."""

    digest = hashlib.sha256(
        f"{salt}|{row.source_file}|{row.source_line}".encode("utf-8")
    ).hexdigest()
    return int(digest[:8], 16) / 2**32


def _bucket_order_key(item: tuple[float, ViewerRow]) -> tuple[float, str, int]:
    """The one deterministic ordering every split decision ties back to."""

    return item[0], item[1].source_file, item[1].source_line


def _eval_keys_by_factory(
    rows: Sequence[ViewerRow], *, eval_fraction: float, salt: str
) -> set[tuple[str, int]]:
    """Select the per-factory eval side, keeping both sides of each factory."""

    by_factory: dict[str, list[tuple[float, ViewerRow]]] = {}
    for row in rows:
        parts = row.source_file.split("/")
        factory = parts[2] if len(parts) > 3 else parts[-1]
        by_factory.setdefault(factory, []).append((split_bucket(row, salt), row))

    evaluation: set[tuple[str, int]] = set()
    for factory in sorted(by_factory):
        ordered = sorted(by_factory[factory], key=_bucket_order_key)
        chosen = _factory_choice_with_both_sides(
            ordered,
            [item for item in ordered if item[0] < eval_fraction],
        )
        evaluation.update((row.source_file, row.source_line) for _bucket, row in chosen)
    return evaluation


def _factory_choice_with_both_sides(
    ordered: list[tuple[float, ViewerRow]], chosen: list[tuple[float, ViewerRow]]
) -> list[tuple[float, ViewerRow]]:
    """Clamp a factory's eval choice so neither of its sides ends up empty."""

    if len(ordered) < 2:
        return chosen
    if not chosen:
        return ordered[:1]
    if len(chosen) == len(ordered):
        return ordered[:-1]
    return chosen


def _rebalance_one_sided_split(
    rows: Sequence[ViewerRow], evaluation: set[tuple[str, int]], salt: str
) -> None:
    """Global hash-order fallback keeping both split sides nonempty."""

    globally_ordered = sorted(
        ((split_bucket(row, salt), row) for row in rows),
        key=_bucket_order_key,
    )
    if not evaluation:
        _bucket, row = globally_ordered[0]
        evaluation.add((row.source_file, row.source_line))
    elif len(evaluation) == len(rows):
        _bucket, row = globally_ordered[-1]
        evaluation.remove((row.source_file, row.source_line))


def _validate_split_request(rows: Sequence[ViewerRow], eval_fraction: float) -> None:
    """Reject requests that cannot produce a meaningful two-sided split."""

    if not 0 < eval_fraction < 1:
        raise ExportError("eval_fraction must be between 0 and 1 exclusive")
    if len(rows) < 2:
        raise ExportError("refusing to split a corpus with fewer than two records")


def _partition_by_eval_keys(
    rows: Sequence[ViewerRow], evaluation: set[tuple[str, int]]
) -> tuple[list[ViewerRow], list[ViewerRow]]:
    """Materialize both split sides from the authenticated row identities."""

    train = [row for row in rows if (row.source_file, row.source_line) not in evaluation]
    evaluate = [row for row in rows if (row.source_file, row.source_line) in evaluation]
    if not train or not evaluate:  # defensive: request validation makes this unreachable
        raise ExportError("deterministic fallback failed to produce both split sides")
    return train, evaluate


def split_rows(
    rows: Sequence[ViewerRow], *, eval_fraction: float, salt: str
) -> tuple[list[ViewerRow], list[ViewerRow]]:
    """Partition one immutable snapshot deterministically, with two-sided fallback."""

    _validate_split_request(rows, eval_fraction)
    evaluation = _eval_keys_by_factory(rows, eval_fraction=eval_fraction, salt=salt)
    _rebalance_one_sided_split(rows, evaluation, salt)
    return _partition_by_eval_keys(rows, evaluation)


if __package__:
    _expose_package_sibling(__name__)
