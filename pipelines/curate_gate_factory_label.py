#!/usr/bin/env python3
"""Fail closed when a cleaned record's factory label disagrees with its path.

``run_gates`` used to take the factory from the file path alone
(``curate_gate_review`` strata, ``curate_gate_identity_gate`` canonical ids)
and never compared that slug with the record. A thalamic file could carry
``meta.factory`` naming another factory, or an id prefix whose reviewed home
is another factory, and still integrate.

This gate reads each cleaned record after composition:

* ``meta.factory``, when the payload states one (wrapper, or the preference
  sides the rest of the mill code already treats as the declaration), must
  not name a different factory than the slug of the file path.
* The record id's mill prefix, when ``REVIEWED_MILL_PREFIX_HOMES`` already
  maps that prefix, must not name a different factory than that same slug.
  A prefix with no reviewed mapping is not evidence. This gate does not
  infer a home from the corpus.

A string in ``meta.factory`` is a factory label when the registry, the
reviewed mill homes, this cleaned tree's own factory directories, or the
``*-factory`` directory convention already names it. Anything else (the
gate fixture's ``"fixture"`` placeholder) does not name a factory, so it
is not a disagreement and is not turned into one.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_factory_label")
    from . import curate_gate_digest as _digest
    from . import curate_gate_records as _records
    from . import curate_identity
    from .mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    from .mill_signals import declared_factory_claims, mill_prefix
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_factory_label"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_digest as _digest
    import curate_gate_records as _records
    import curate_identity
    from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    from mill_signals import declared_factory_claims, mill_prefix

FACTORY_LABEL_GATE = "factory_label"
FACTORY_LABEL_MISMATCH = "FACTORY_LABEL_MISMATCH"
_EXAMPLE_LIMIT = 5

jsonl_paths = _digest.jsonl_paths
iter_records = _records.iter_records


def path_factory(relative: str) -> str:
    """The factory slug ``curate_gate_review`` derives from a corpus path."""

    return relative.split("/", 1)[0] if "/" in relative else "_root"


def _registry_labels() -> set[str]:
    labels: set[str] = set()
    for row in curate_identity.default_registry().by_path_id.values():
        labels.add(row.path_id)
        labels.add(row.payload_factory)
    return labels


def _tree_labels(cleaned: Path) -> set[str]:
    labels: set[str] = set()
    for path in jsonl_paths(cleaned):
        labels.add(path_factory(path.relative_to(cleaned).as_posix()))
    return labels


def known_factory_labels(cleaned: Path) -> frozenset[str]:
    """Factory identities this repository already has a name for."""

    labels = set(REVIEWED_MILL_PREFIX_HOMES.values())
    labels.update(_registry_labels())
    labels.update(_tree_labels(cleaned))
    return frozenset(labels)


def _names_a_factory(claim: str, known: frozenset[str]) -> bool:
    if claim in known:
        return True
    return len(claim) > len("-factory") and claim.endswith("-factory")


def _meta_conflicts(record: Any, path_slug: str, known: frozenset[str]) -> tuple[str, ...]:
    conflicts: list[str] = []
    for claim in declared_factory_claims(record):
        if claim == path_slug or claim in conflicts:
            continue
        if _names_a_factory(claim, known):
            conflicts.append(claim)
    return tuple(conflicts)


def _prefix_conflict(record: Any, path_slug: str) -> tuple[str, str] | None:
    """The reviewed home of this id prefix, when that home is another factory.

    No reviewed mapping means no prefix evidence. Homes are not inferred.
    """

    prefix = mill_prefix(record)
    if prefix is None:
        return None
    home = REVIEWED_MILL_PREFIX_HOMES.get(prefix)
    if home is None or home == path_slug:
        return None
    return prefix, home


def _mismatch(
    relative: str,
    number: int,
    record: Any,
    known: frozenset[str],
) -> dict[str, Any] | None:
    if not isinstance(record, dict):
        return None
    path_slug = path_factory(relative)
    meta = _meta_conflicts(record, path_slug, known)
    prefix = _prefix_conflict(record, path_slug)
    if not meta and prefix is None:
        return None
    finding: dict[str, Any] = {
        "source": f"{relative}:{number}",
        "path_factory": path_slug,
    }
    if meta:
        finding["meta_factory"] = list(meta)
    if prefix is not None:
        finding["id_prefix"] = prefix[0]
        finding["prefix_home"] = prefix[1]
    return finding


def factory_label_gate(cleaned: Path) -> dict[str, Any]:
    """Report records whose factory label disagrees with the file-path slug."""

    known = known_factory_labels(Path(cleaned))
    mismatches: list[dict[str, Any]] = []
    for relative, number, record in iter_records(Path(cleaned)):
        finding = _mismatch(relative, number, record, known)
        if finding is not None:
            mismatches.append(finding)
    return {
        "passed": not mismatches,
        "count": len(mismatches),
        "examples": mismatches[:_EXAMPLE_LIMIT],
    }


if __package__:
    _expose_package_sibling(__name__)
