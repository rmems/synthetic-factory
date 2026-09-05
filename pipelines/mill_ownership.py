#!/usr/bin/env python3
"""Sequence the ownership axes into one export-safety verdict for a run.

``mill_resolution.py`` builds the per-run maps and ``mill_evidence.py`` judges
one entry against them; this module runs the phases in order and decides
whether cross-factory ownership is resolved well enough to write a cleaned
tree. It owns the read-only context passed down to the per-entry pass and the
report dictionary callers consume.

Split out of ``mill_family.py``: the phase order, the branch order inside
``resolve_entry_goal_ownership``, and every early exit are unchanged.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

if __package__:
    from .mill_evidence import (
        GOAL_FAMILY_MIN_FOREIGN_TOKENS,
        GOAL_FAMILY_MIN_SUPPORT,
        Axes,
        Entry,
        entry_label,
        foreignness,
        is_novel_unreviewed_goal,
        raw_goal_family_home,
    )
    from .mill_resolution import (
        ambiguous_goal_tokens,
        count_goal_tokens,
        declared_identity,
        goal_family_homes,
        goal_vocabulary,
        missing_homes,
        prefix_homes,
        reference_scope_state,
        unresolved_ambiguous_signatures,
        unresolved_destinations,
        unresolved_prefixes,
        verified_factories,
    )
    from .mill_reviewed_vocabulary import REVIEWED_GOAL_TOKEN_HOMES
else:
    from mill_evidence import (
        GOAL_FAMILY_MIN_FOREIGN_TOKENS,
        GOAL_FAMILY_MIN_SUPPORT,
        Axes,
        Entry,
        entry_label,
        foreignness,
        is_novel_unreviewed_goal,
        raw_goal_family_home,
    )
    from mill_resolution import (
        ambiguous_goal_tokens,
        count_goal_tokens,
        declared_identity,
        goal_family_homes,
        goal_vocabulary,
        missing_homes,
        prefix_homes,
        reference_scope_state,
        unresolved_ambiguous_signatures,
        unresolved_destinations,
        unresolved_prefixes,
        verified_factories,
    )
    from mill_reviewed_vocabulary import REVIEWED_GOAL_TOKEN_HOMES


@dataclass(frozen=True)
class OwnershipResolutionContext:
    """Read-only per-run context shared by every entry in one ownership pass.

    Bundles the values ``ownership_context`` resolves once before its
    per-entry loop, so the loop body can be a named helper. Every field here
    is exactly one local ``ownership_context`` already computed; nothing is
    recomputed or reshaped.
    """

    axes: Axes
    goal_homes: Mapping[Entry, str]
    raw_goal_candidates: Mapping[Entry, tuple[str, frozenset[str]]]
    raw_goal_candidate_support: Mapping[tuple[str, str, frozenset[str]], int]
    reference_scope_complete: bool
    ambiguous_goal_signatures: Mapping[Entry, frozenset[str]]
    unresolved_ambiguous_signatures: frozenset[frozenset[str]]
    reviewed_goal_tokens: frozenset[str]
    verified: set[str]


@dataclass(frozen=True)
class AmbiguousSignatureAccumulator:
    """Mutable output pair for the ambiguous-goal-signature collection pass."""

    signatures: dict[Entry, frozenset[str]]
    support: dict[frozenset[str], Counter[str]]


@dataclass(frozen=True)
class OwnershipFindings:
    """Mutable output pair the per-entry ownership pass writes into."""

    unresolved_goal_records: set[str]
    absent_homes: set[str | None]


@dataclass(frozen=True)
class _EntryResolution:
    """One entry plus the two values every branch of its pass needs."""

    entry: Entry
    effective_factory: str
    anchored_home: str | None


# -- collection passes -------------------------------------------------


def collect_raw_goal_candidate(
    entry: Entry,
    axes: Axes,
    raw_goal_candidates: dict[Entry, tuple[str, frozenset[str]]],
    raw_goal_candidate_support: Counter[tuple[str, str, frozenset[str]]],
) -> None:
    """Record one entry's raw (unanchored) goal-family candidate, if any."""

    factory = axes.identity.get(entry.factory) or entry.factory
    candidate = raw_goal_family_home(
        entry,
        axes.vocabulary,
        factory,
        require_independent_anchor=False,
    )
    if candidate is None:
        return
    candidate_signature = frozenset(
        entry.goal_family & axes.vocabulary[candidate]
    )
    raw_goal_candidates[entry] = (candidate, candidate_signature)
    payload_foreign, prefix_foreign, _ = foreignness(entry, axes)
    if not payload_foreign and not prefix_foreign:
        raw_goal_candidate_support[
            (factory, candidate, candidate_signature)
        ] += 1


def collect_ambiguous_goal_signature(
    entry: Entry,
    axes: Axes,
    ambiguous_tokens: frozenset[str],
    accumulator: AmbiguousSignatureAccumulator,
) -> None:
    """Record one entry's ambiguous-goal-token signature, if it has one."""

    payload_foreign, prefix_foreign, effective_factory = foreignness(entry, axes)
    if payload_foreign or prefix_foreign:
        return
    signature = frozenset(entry.goal_family & ambiguous_tokens)
    if len(signature) < GOAL_FAMILY_MIN_FOREIGN_TOKENS:
        return
    accumulator.signatures[entry] = signature
    accumulator.support[signature][effective_factory] += 1


# -- per-entry resolution ----------------------------------------------


def _note_unresolved(
    state: _EntryResolution,
    home: str | None,
    context: OwnershipResolutionContext,
    found: OwnershipFindings,
) -> None:
    """Mark one entry unresolved, naming any home absent from ``verified``."""

    found.unresolved_goal_records.add(entry_label(state.entry))
    if home is not None and home not in context.verified:
        found.absent_homes.add(home)


def _repeated_generic_cohort_home(
    state: _EntryResolution, context: OwnershipResolutionContext
) -> str | None:
    """Return this entry's cohort home when it is a repeated generic match.

    A raw candidate with no independent anchor, seen on at least
    ``GOAL_FAMILY_MIN_SUPPORT`` records of the same destination/signature
    cohort. Repeated generic reviewed terms are insufficient to quarantine a
    record, but they are also not permission to export it.
    """

    candidate = context.raw_goal_candidates.get(state.entry)
    if candidate is None:
        return None
    if state.anchored_home is not None:
        return None
    candidate_home, candidate_signature = candidate
    support = context.raw_goal_candidate_support[
        (state.effective_factory, candidate_home, candidate_signature)
    ]
    return candidate_home if support >= GOAL_FAMILY_MIN_SUPPORT else None


def _is_novel_here(
    state: _EntryResolution, context: OwnershipResolutionContext
) -> bool:
    """True when this goal's unreviewed vocabulary is too novel to resolve."""

    return is_novel_unreviewed_goal(
        state.entry, state.effective_factory, context.reviewed_goal_tokens
    )


def _resolve_under_complete_scope(
    state: _EntryResolution,
    context: OwnershipResolutionContext,
    found: OwnershipFindings,
) -> None:
    """Resolve one entry when every reviewed prefix is covered by the source.

    Full reviewed-prefix coverage does not resolve a novel goal family
    repeated in multiple factories -- those tokens were deliberately omitted
    from ``vocabulary`` as ambiguous. Nor is covering every reviewed prefix
    independent evidence for a novel family that self-taught one destination.
    Keep both unresolved instead of reading the omission as permission to
    export them.
    """

    ambiguous = context.ambiguous_goal_signatures.get(state.entry)
    if ambiguous in context.unresolved_ambiguous_signatures:
        found.unresolved_goal_records.add(entry_label(state.entry))
        return
    if _is_novel_here(state, context):
        found.unresolved_goal_records.add(entry_label(state.entry))


def _resolve_under_partial_scope(
    state: _EntryResolution,
    context: OwnershipResolutionContext,
    found: OwnershipFindings,
) -> None:
    """Resolve one entry when the reviewed reference scope is incomplete.

    A singleton can resemble a reviewed foreign family while still being a
    legitimate cross-domain task. Do not quarantine it on that resemblance
    alone, but do fail a partial export closed: the complete audited
    reference scope is what establishes that the singleton is not part of a
    repeated foreign cohort.
    """

    if state.anchored_home is not None:
        _note_unresolved(state, state.anchored_home, context, found)
        return
    if _is_novel_here(state, context):
        found.unresolved_goal_records.add(entry_label(state.entry))


def resolve_entry_goal_ownership(
    entry: Entry,
    context: OwnershipResolutionContext,
    found: OwnershipFindings,
) -> None:
    """Apply one entry's goal-ownership resolution, in place.

    Same branches, same order, same early exits as the per-entry pass in
    ``ownership_context``.
    """

    payload_foreign, prefix_foreign, effective_factory = foreignness(
        entry, context.axes
    )
    if payload_foreign or prefix_foreign:
        return

    goal_home = context.goal_homes.get(entry)
    if goal_home is not None:
        if goal_home not in context.verified:
            found.absent_homes.add(goal_home)
        return

    state = _EntryResolution(
        entry=entry,
        effective_factory=effective_factory,
        anchored_home=raw_goal_family_home(
            entry, context.axes.vocabulary, effective_factory
        ),
    )
    cohort_home = _repeated_generic_cohort_home(state, context)
    if cohort_home is not None:
        _note_unresolved(state, cohort_home, context, found)
        return

    if context.reference_scope_complete:
        _resolve_under_complete_scope(state, context, found)
        return

    _resolve_under_partial_scope(state, context, found)


# -- orchestration -----------------------------------------------------


def _collect_raw_goal_candidates(
    entries: Sequence[Entry], axes: Axes
) -> tuple[
    dict[Entry, tuple[str, frozenset[str]]],
    Counter[tuple[str, str, frozenset[str]]],
]:
    """Run the raw-goal-candidate pass over every entry."""

    candidates: dict[Entry, tuple[str, frozenset[str]]] = {}
    support: Counter[tuple[str, str, frozenset[str]]] = Counter()
    for entry in entries:
        collect_raw_goal_candidate(entry, axes, candidates, support)
    return candidates, support


def _collect_ambiguous_signatures(
    entries: Sequence[Entry],
    axes: Axes,
    ambiguous_tokens: frozenset[str],
) -> AmbiguousSignatureAccumulator:
    """Run the ambiguous-goal-signature pass over every entry."""

    accumulator = AmbiguousSignatureAccumulator(
        signatures={}, support=defaultdict(Counter)
    )
    for entry in entries:
        collect_ambiguous_goal_signature(
            entry, axes, ambiguous_tokens, accumulator
        )
    return accumulator


def _build_context(
    entries: Sequence[Entry],
    axes: Axes,
    goal_token_counts: Mapping[str, Counter[str]],
    scope: tuple[bool, set[str]],
) -> OwnershipResolutionContext:
    """Resolve every per-run value the per-entry pass reads."""

    reference_scope_complete, verified = scope
    raw_goal_candidates, raw_goal_candidate_support = (
        _collect_raw_goal_candidates(entries, axes)
    )
    reviewed_goal_tokens = frozenset(REVIEWED_GOAL_TOKEN_HOMES)
    ambiguous = _collect_ambiguous_signatures(
        entries,
        axes,
        ambiguous_goal_tokens(goal_token_counts, reviewed_goal_tokens),
    )
    return OwnershipResolutionContext(
        axes=axes,
        goal_homes=goal_family_homes(entries, axes),
        raw_goal_candidates=raw_goal_candidates,
        raw_goal_candidate_support=raw_goal_candidate_support,
        reference_scope_complete=reference_scope_complete,
        ambiguous_goal_signatures=ambiguous.signatures,
        unresolved_ambiguous_signatures=unresolved_ambiguous_signatures(
            ambiguous.support
        ),
        reviewed_goal_tokens=reviewed_goal_tokens,
        verified=verified,
    )


def resolve_axes(entries: Sequence[Entry]) -> tuple[Axes, dict[str, Counter[str]]]:
    """Build the run's identity, prefix-home and goal-vocabulary maps, in order."""

    identity = declared_identity(entries)
    axes = Axes(identity=identity, homes=prefix_homes(entries, identity))
    goal_token_counts = count_goal_tokens(entries, axes)
    vocabulary = goal_vocabulary(
        entries, axes, goal_token_counts=goal_token_counts
    )
    return replace(axes, vocabulary=vocabulary), goal_token_counts


def _report(
    entries: Sequence[Entry],
    context: OwnershipResolutionContext,
    found: OwnershipFindings,
    prefix_factories: Mapping[str, set[str]],
) -> dict[str, Any]:
    """Assemble the ownership verdict from a completed pass."""

    unresolved_dests = unresolved_destinations(
        {entry.factory for entry in entries}, context.axes.identity
    )
    unresolved_prefix_names = unresolved_prefixes(
        prefix_factories, context.axes.homes
    )
    found.absent_homes.discard(None)
    complete = (
        len(context.verified) >= 2
        and not unresolved_dests
        and not unresolved_prefix_names
        and not found.absent_homes
        and not found.unresolved_goal_records
    )
    return {
        "complete": complete,
        "reference_scope_complete": context.reference_scope_complete,
        "verified_factories": sorted(context.verified),
        "unresolved_destinations": unresolved_dests,
        "unresolved_prefixes": unresolved_prefix_names,
        "unresolved_goal_records": sorted(found.unresolved_goal_records),
        "missing_home_factories": sorted(found.absent_homes),
    }


def ownership_context(entries: Sequence[Entry]) -> dict[str, Any]:
    """Describe whether cross-factory ownership is safe for output.

    Curation may report an incomplete source, but it must not write a
    cleaned tree when any ownership axis is unresolved or when a signal
    names a home factory absent from the verified source context. Partial
    sources apply the stricter reviewed-signature boundary; a source that
    contains every reviewed factory may use the complete corpus as its
    reference index.
    """

    verified = verified_factories(entries)
    reference_scope_complete, prefix_factories = reference_scope_state(entries)
    axes, goal_token_counts = resolve_axes(entries)

    context = _build_context(
        entries,
        axes,
        goal_token_counts,
        (reference_scope_complete, verified),
    )
    found = OwnershipFindings(
        unresolved_goal_records=set(),
        absent_homes=missing_homes(entries, axes, verified),
    )
    for entry in entries:
        resolve_entry_goal_ownership(entry, context, found)

    return _report(entries, context, found, prefix_factories)
