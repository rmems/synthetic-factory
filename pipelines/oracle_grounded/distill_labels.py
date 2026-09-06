#!/usr/bin/env python3
"""Family-owned oracle-label policies for the distillation contract (D2).

The shared ``ORACLE_ONLY_KEYS`` scan in ``distill_blocks`` is structural: one
frozen set for every family, compared by exact key name inside the
generator-owned sections. It cannot know that ``preferred`` is the energy
oracle's verdict or that ``trace_summary`` is the fault oracle's trace, and
growing the shared set for every family label would never end. Decision D2
(2026-09-05): each family declares the keys its oracle writes as labels, in
code the family owns, and a family check refuses those keys anywhere inside
the generator-owned sections.

Three rules shape this module.

* **Declarations are trusted code, never record content.** A policy is
  registered by the family module through :func:`declare_oracle_labels` or
  handed to the check as an :class:`OracleLabelPolicy`. Nothing in the record
  being validated can supply, extend or shrink it; the record's ``family`` is
  only the lookup key.
* **A missing policy is a finding, not a skip.** A validator that reaches
  this check for a family with no declaration reports
  ``ORACLE_LABEL_POLICY_MISSING``, so full validation is visibly incomplete
  rather than silently reduced to the structural checks.
* **Distinct from structural validation and curation.** ``check_envelope``
  does not call this check and ``curation_eligible`` sees it only through the
  findings the caller passes in; a composing validator runs all three.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from . import distill_vocabulary as vocab
from . import envelope
from .import_twins import bind_import_twin

POLICY_MISSING = "ORACLE_LABEL_POLICY_MISSING"
POLICY_MISMATCH = "ORACLE_LABEL_POLICY_MISMATCH"
LABEL_IN_GENERATOR_NAMESPACE = "ORACLE_LABEL_IN_GENERATOR_NAMESPACE"


@dataclass(frozen=True)
class OracleLabelPolicy:
    """The keys a family's oracle writes as labels, declared by that family."""

    family: str
    label_keys: frozenset[str]

    def __post_init__(self) -> None:
        _refuse_unknown_family(self.family)
        _refuse_label_keys(self.family, self.label_keys)


def _refuse_unknown_family(family: Any) -> None:
    if family not in vocab.FAMILIES:
        raise envelope.ContractError(f"unknown family for an oracle-label policy: {family!r}")


def _refuse_label_keys(family: str, keys: Any) -> None:
    """A non-empty frozenset of non-empty key names, and nothing else."""

    if not isinstance(keys, frozenset) or not keys:
        raise envelope.ContractError(
            f"{family}: label_keys must be a non-empty frozenset of key names"
        )
    if any(vocab.missing_string(key) for key in keys):
        raise envelope.ContractError(f"{family}: every oracle-label key must be a non-empty string")


_POLICIES: dict[str, OracleLabelPolicy] = {}


def declare_oracle_labels(family: str, label_keys: Iterable[str]) -> OracleLabelPolicy:
    """Register a family's declaration; idempotent for the same set, refused for another.

    Called from the family's own module, so the declaration is code the family
    owns and reviews, not data a record carries.
    """

    if isinstance(label_keys, (str, bytes)):
        raise envelope.ContractError(
            f"{family}: label_keys must be an iterable of key names, not one string"
        )
    policy = OracleLabelPolicy(family, frozenset(label_keys))
    existing = _POLICIES.get(family)
    if existing is not None:
        if existing != policy:
            raise envelope.ContractError(
                f"{family}: an oracle-label policy is already declared with a different key set"
            )
        return existing
    _POLICIES[family] = policy
    return policy


def oracle_label_policy(family: Any) -> OracleLabelPolicy | None:
    """The trusted declaration for ``family``, or ``None`` when it has none."""

    if not isinstance(family, str):
        return None
    return _POLICIES.get(family)


def declared_families() -> tuple[str, ...]:
    """The families that have declared an oracle-label policy."""

    return tuple(sorted(_POLICIES))


def _hit_listing(hits: list[str]) -> str:
    listed = ", ".join(sorted(hits))
    if len(hits) >= envelope.MAX_RESERVED_KEY_HITS:
        listed += ", ... (scan capped)"
    return listed


def check_oracle_label_leak(
    record: Any, where: str, *, policy: OracleLabelPolicy | None = None
) -> list[str]:
    """Family validation: no label of this family's oracle inside a generator section.

    ``policy`` is the family's trusted declaration. When omitted it is looked
    up by ``record["family"]``; the key set itself never comes from the
    record. The walk is the envelope's bounded reserved-key scan over every
    generator-owned section, dicts and lists alike, compared by exact key
    name, so ``predicted_outcome`` is not ``outcome``.
    """

    if not isinstance(record, dict):
        return [f"{where}: record must be an object"]
    family = record.get("family")
    active = policy if policy is not None else oracle_label_policy(family)
    problem = _policy_problem(active, family, where)
    if problem is None:
        problem = _leak_finding(record, active, where)
    return [] if problem is None else [problem]


def _policy_problem(active: OracleLabelPolicy | None, family: Any, where: str) -> str | None:
    """Why no leak check can run: no declaration for the family, or the wrong one."""

    if active is None:
        return (
            f"{where}: {POLICY_MISSING} — family {family!r} declares no oracle-label "
            "policy, so full validation cannot run"
        )
    if family != active.family:
        return (
            f"{where}: {POLICY_MISMATCH} — record family {family!r} is not the "
            f"{active.family!r} policy it was checked against"
        )
    return None


def _leak_finding(record: dict[str, Any], active: OracleLabelPolicy, where: str) -> str | None:
    """The leak finding for this record under ``active``, or None when it is clean."""

    try:
        hits = envelope.reserved_key_hits(record, active.label_keys)
    except RecursionError:
        return vocab.scan_depth_finding(where)
    if not hits:
        return None
    return (
        f"{where}: {LABEL_IN_GENERATOR_NAMESPACE} at {_hit_listing(hits)} (generator "
        f"sections carry keys only the {active.family} oracle may write)"
    )


bind_import_twin(__name__)
