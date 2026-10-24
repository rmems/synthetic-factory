#!/usr/bin/env python3
"""Fail closed when a cleaned record's factory label disagrees with its path.

``run_gates`` used to take the factory from the file path alone
(``curate_gate_review`` strata, ``curate_gate_identity_gate`` canonical ids)
and never compared that slug with the record. A thalamic file could carry
``meta.factory`` naming another factory and still integrate.

This gate reads each cleaned record after composition:

* ``meta.factory``, when the payload states one (wrapper, or the preference
  sides the rest of the mill code already treats as the declaration) and
  that value names a different known factory than the file-path slug, fails
  the gate. ``FACTORY_LABEL_MISMATCH`` is raised only for that disagreement.
* The record id's mill prefix, when ``REVIEWED_MILL_PREFIX_HOMES`` already
  maps that prefix to another factory, is recorded as a non-blocking note.
  A borrowed prefix whose ``meta.factory`` matches the folder (``dbc-``
  inside ``api-contract-migration-factory``) does not fail the gate. A
  prefix with no reviewed mapping is not evidence. This gate does not
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


def _label_finding(
    relative: str,
    number: int,
    record: Any,
    known: frozenset[str],
) -> dict[str, Any] | None:
    """One record's meta disagreement and any borrowed-prefix note.

    A finding blocks only when ``meta_factory`` is present. A reviewed
    prefix whose home is another factory is attached either to that
    blocking finding or, when ``meta.factory`` agrees with the path, as a
    note by itself.
    """

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


def _is_blocking(finding: dict[str, Any]) -> bool:
    return "meta_factory" in finding


def factory_label_gate(cleaned: Path) -> dict[str, Any]:
    """Report records whose ``meta.factory`` disagrees with the file-path slug.

    A reviewed id prefix that names another factory is listed under
    ``prefix_notes`` and does not fail the gate on its own. Examples and
    notes keep the first ``_EXAMPLE_LIMIT`` findings; ``count`` and
    ``prefix_note_count`` still cover the whole corpus.
    """

    known = known_factory_labels(Path(cleaned))
    mismatches = 0
    notes = 0
    examples: list[dict[str, Any]] = []
    prefix_notes: list[dict[str, Any]] = []
    for relative, number, record in iter_records(Path(cleaned)):
        finding = _label_finding(relative, number, record, known)
        if finding is None:
            continue
        if _is_blocking(finding):
            mismatches += 1
            if len(examples) < _EXAMPLE_LIMIT:
                examples.append(finding)
        else:
            notes += 1
            if len(prefix_notes) < _EXAMPLE_LIMIT:
                prefix_notes.append(finding)
    return {
        "passed": mismatches == 0,
        "count": mismatches,
        "examples": examples,
        "prefix_notes": prefix_notes,
        "prefix_note_count": notes,
    }


if __package__:
    _expose_package_sibling(__name__)
