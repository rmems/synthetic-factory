#!/usr/bin/env python3
"""Resolve the three ownership axes across a whole run of indexed entries.

Where ``mill_evidence.py`` judges one entry against an already-resolved
``Axes``, this module builds that ``Axes``: which factory each destination
really is, where each mill id prefix lives, and which goal vocabulary is
characteristic of which destination. Every function takes the full entry
sequence and returns a map; none of them decide whether a record is foreign.

Split out of ``mill_family.py``: each function is the former ``MillIndex``
method of the same name without its leading underscore, taking ``entries``
where it used to read ``self._entries``.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence

from mill_evidence import (
    GOAL_FAMILY_MIN_SUPPORT,
    Axes,
    Entry,
    foreignness,
    raw_goal_family_home,
)
from mill_reviewed_vocabulary import (
    REVIEWED_GOAL_TOKEN_HOMES,
    REVIEWED_MILL_PREFIX_HOMES,
)


def verified_factories(entries: Sequence[Entry]) -> set[str]:
    """Return every destination whose identity the caller established directly."""

    return {entry.factory for entry in entries if entry.factory_verified}


# -- destination identity ---------------------------------------------


def resolve_unverified_identity(
    factory: str, per_declared: Counter[str]
) -> str | None:
    """Return the payload-declared identity for one unverified destination.

    A declaration matching the directory's own name is independent native
    evidence, preferred over a majority that may consist of foreign or
    otherwise poisoned records. Snapshot/off-slug roots fall back to the
    unique most common declaration.
    """

    if factory in per_declared:
        return factory
    top = max(per_declared.values())
    winners = [name for name, seen in per_declared.items() if seen == top]
    return winners[0] if len(winners) == 1 else None


def _declaration_counts(entries: Sequence[Entry]) -> dict[str, Counter[str]]:
    """Count, per destination, the factory each of its payloads declares."""

    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for entry in entries:
        if entry.declared_factory is not None:
            counts[entry.factory][entry.declared_factory] += 1
    return counts


def declared_identity(entries: Sequence[Entry]) -> dict[str, str | None]:
    """Map each destination to the single factory its payloads declare.

    Compared against the payloads rather than the directory name so that
    the check holds for snapshots, staging copies, and fixtures whose
    directory is not named after a factory slug.
    """

    verified = verified_factories(entries)
    identity: dict[str, str | None] = {factory: factory for factory in verified}
    for factory, per_declared in _declaration_counts(entries).items():
        if factory in verified:
            continue
        identity[factory] = resolve_unverified_identity(factory, per_declared)
    return identity


def unresolved_destinations(
    destinations: Iterable[str],
    identity: Mapping[str, str | None],
) -> list[str]:
    """Return destinations ``declared_identity`` could not resolve."""

    return sorted(
        factory for factory in destinations if identity.get(factory) is None
    )


# -- mill id prefixes --------------------------------------------------


def resolve_prefix_home(
    prefix: str, per_factory: Counter[str], declared: set[str]
) -> frozenset[str]:
    """Return the resolved home(s) for one mill prefix.

    A reviewed alias wins outright; otherwise one consistent payload
    declaration wins; otherwise a prefix seen under exactly one factory is
    local to it; otherwise the prefix has no inferred home.
    """

    reviewed_home = REVIEWED_MILL_PREFIX_HOMES.get(prefix)
    if reviewed_home is not None:
        return frozenset({reviewed_home})
    if len(declared) == 1:
        return frozenset(declared)
    if len(per_factory) == 1:
        return frozenset(per_factory)
    return frozenset()


def _prefix_evidence(
    entries: Sequence[Entry],
    identity: Mapping[str, str | None] | None,
) -> tuple[dict[str, Counter[str]], dict[str, set[str]]]:
    """Gather, per prefix, where it was seen and what its records declare."""

    counts: dict[str, Counter[str]] = defaultdict(Counter)
    declarations: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        if entry.mill_prefix is None:
            continue
        resolved = identity.get(entry.factory) if identity is not None else None
        counts[entry.mill_prefix][resolved or entry.factory] += 1
        if entry.declared_factory is not None:
            declarations[entry.mill_prefix].add(entry.declared_factory)
    return counts, declarations


def prefix_homes(
    entries: Sequence[Entry],
    identity: Mapping[str, str | None] | None = None,
) -> dict[str, frozenset[str]]:
    """Map prefixes to homes supported by independent evidence.

    A maximum share is not ownership: one rare native alias can have a
    lower within-factory share than one spill in a smaller destination.
    Prefer a reviewed alias or one consistent payload declaration. A
    prefix observed in only one factory is local. Conflicting declarations
    across factories intentionally have no inferred home; destination
    purity is not independent evidence and cannot resolve the conflict.
    """

    counts, declarations = _prefix_evidence(entries, identity)
    return {
        prefix: resolve_prefix_home(prefix, per_factory, declarations[prefix])
        for prefix, per_factory in counts.items()
    }


def reference_scope_state(
    entries: Sequence[Entry],
) -> tuple[bool, dict[str, set[str]]]:
    """Return (reference_scope_complete, prefix_factories).

    Whether every reviewed prefix is covered by a verified entry naming its
    reviewed home, plus which factories each mill prefix was seen under.
    """

    reviewed_prefix_coverage = {
        (entry.mill_prefix, entry.factory)
        for entry in entries
        if entry.factory_verified
        and entry.mill_prefix is not None
        and REVIEWED_MILL_PREFIX_HOMES.get(entry.mill_prefix) == entry.factory
    }
    reference_scope_complete = all(
        (prefix, home) in reviewed_prefix_coverage
        for prefix, home in REVIEWED_MILL_PREFIX_HOMES.items()
    )
    prefix_factories: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        if entry.mill_prefix is not None:
            prefix_factories[entry.mill_prefix].add(entry.factory)
    return reference_scope_complete, prefix_factories


def unresolved_prefixes(
    prefix_factories: Mapping[str, set[str]],
    homes: Mapping[str, frozenset[str]],
) -> list[str]:
    """Return mill prefixes with no clean single-factory resolution.

    A prefix is unresolved when it is not a reviewed alias, or when it was
    seen under more than one factory and has no resolved home.
    """

    return sorted(
        prefix
        for prefix, factories in prefix_factories.items()
        if prefix not in REVIEWED_MILL_PREFIX_HOMES
        or (len(factories) > 1 and not homes.get(prefix))
    )


def missing_homes(
    entries: Sequence[Entry],
    axes: Axes,
    verified: set[str],
) -> set[str | None]:
    """Return every home factory named by a signal but absent from ``verified``.

    The three-part union: prefix homes, resolved destination identities, and
    verified entries' own disagreeing declarations.
    """

    absent = {
        home
        for homes_for_prefix in axes.homes.values()
        for home in homes_for_prefix
        if home not in verified
    }
    absent.update(
        expected
        for expected in axes.identity.values()
        if expected is not None and expected not in verified
    )
    absent.update(
        claim
        for entry in entries
        if entry.factory_verified
        for claim in entry.declared_claims
        if claim != entry.factory and claim not in verified
    )
    return absent


# -- goal vocabulary ---------------------------------------------------


def count_goal_tokens(
    entries: Sequence[Entry], axes: Axes
) -> dict[str, Counter[str]]:
    """Count goal tokens using only records not known to be foreign.

    A record already known to come from elsewhere must not teach this
    destination its vocabulary. An empty prefix home set means the prefix is
    unresolved, not foreign; such a record may still teach the destination
    for report-only analysis while output stays blocked by
    ``unresolved_prefixes``.
    """

    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for entry in entries:
        payload_foreign, prefix_foreign, factory = foreignness(entry, axes)
        if payload_foreign or prefix_foreign:
            continue
        for token in entry.goal_family:
            counts[token][factory] += 1
    return counts


def _token_owner(token: str, per_factory: Counter[str]) -> str | None:
    """Return the one destination that owns this goal token, if any.

    Reviewed product terms are independent evidence. Any other token needs
    support in exactly one factory, at or above ``GOAL_FAMILY_MIN_SUPPORT``.
    """

    reviewed_home = REVIEWED_GOAL_TOKEN_HOMES.get(token)
    if reviewed_home is not None:
        return reviewed_home
    if len(per_factory) != 1:
        return None
    factory, seen = next(iter(per_factory.items()))
    return factory if seen >= GOAL_FAMILY_MIN_SUPPORT else None


def goal_vocabulary(
    entries: Sequence[Entry],
    axes: Axes,
    *,
    goal_token_counts: Mapping[str, Counter[str]] | None = None,
) -> dict[str, frozenset[str]]:
    """Map each destination to goal tokens uniquely characteristic of it.

    A token observed in more than one factory remains ambiguous regardless of
    prevalence: contaminated records cannot win ownership merely by becoming
    denser.
    """

    counts = (
        count_goal_tokens(entries, axes)
        if goal_token_counts is None
        else goal_token_counts
    )

    vocabulary: dict[str, set[str]] = defaultdict(set)
    for token, per_factory in counts.items():
        owner = _token_owner(token, per_factory)
        if owner is not None:
            vocabulary[owner].add(token)
    return {
        factory: frozenset(tokens) for factory, tokens in vocabulary.items()
    }


def _recurs_across_factories(per_factory: Counter[str]) -> bool:
    """True when a signal is seen in 2+ factories with real support in one."""

    return len(per_factory) >= 2 and any(
        seen >= GOAL_FAMILY_MIN_SUPPORT for seen in per_factory.values()
    )


def ambiguous_goal_tokens(
    goal_token_counts: Mapping[str, Counter[str]],
    reviewed_goal_tokens: frozenset[str],
) -> frozenset[str]:
    """Return goal tokens seen in 2+ factories with enough support to be ambiguous."""

    return frozenset(
        token
        for token, per_factory in goal_token_counts.items()
        if token not in reviewed_goal_tokens
        and _recurs_across_factories(per_factory)
    )


def unresolved_ambiguous_signatures(
    ambiguous_signature_support: Mapping[frozenset[str], Counter[str]],
) -> frozenset[frozenset[str]]:
    """Return ambiguous goal signatures with enough cross-factory support."""

    return frozenset(
        signature
        for signature, per_factory in ambiguous_signature_support.items()
        if _recurs_across_factories(per_factory)
    )


# -- goal-family homes -------------------------------------------------


def _goal_home_candidates(
    entries: Sequence[Entry], axes: Axes
) -> tuple[dict[Entry, str], Counter[tuple[str, str]]]:
    """Return each entry's foreign goal home plus clean destination support.

    Prefix- or payload-foreign records still get a candidate recorded, but
    they never contribute support for a goal-only finding against a native
    record.
    """

    candidates: dict[Entry, str] = {}
    support: Counter[tuple[str, str]] = Counter()
    for entry in entries:
        payload_foreign, prefix_foreign, factory = foreignness(entry, axes)
        goal_home = raw_goal_family_home(entry, axes.vocabulary, factory)
        if goal_home is None:
            continue
        candidates[entry] = goal_home
        if not payload_foreign and not prefix_foreign:
            support[(factory, goal_home)] += 1
    return candidates, support


def _goal_home_is_supported(
    entry: Entry,
    goal_home: str,
    support: Counter[tuple[str, str]],
    axes: Axes,
) -> bool:
    """True when one candidate goal home may stand as a finding.

    Prefix- or payload-foreign records already carry independent ownership
    evidence, so their goal-family detail is retained without the extra
    support threshold.
    """

    payload_foreign, prefix_foreign, factory = foreignness(entry, axes)
    if payload_foreign or prefix_foreign:
        return True
    return support[(factory, goal_home)] >= GOAL_FAMILY_MIN_SUPPORT


def goal_family_homes(
    entries: Sequence[Entry], axes: Axes
) -> dict[Entry, str]:
    """Return supported foreign goal homes without convicting one overlap.

    The same clean destination-to-home signal must recur on at least
    ``GOAL_FAMILY_MIN_SUPPORT`` records. Each candidate independently
    matches at least ``GOAL_FAMILY_MIN_FOREIGN_TOKENS`` terms; tokens are
    never pooled across partial matches.
    """

    candidates, support = _goal_home_candidates(entries, axes)
    return {
        entry: goal_home
        for entry, goal_home in candidates.items()
        if _goal_home_is_supported(entry, goal_home, support, axes)
    }
