#!/usr/bin/env python3
"""Per-entry ownership predicates: does one record's evidence disagree here?

One indexed entry at a time, against an already-resolved picture of the run
(``Axes``: destination identities, prefix homes, goal vocabulary). Every
function here is pure: it reads an ``Entry`` plus that picture and returns an
answer, never accumulating state and never touching the corpus. Building the
picture is ``mill_resolution.py``'s job; sequencing the phases across a whole
run is ``mill_ownership.py``'s.

Split out of ``mill_family.py``: each predicate is the former ``MillIndex``
static method of the same name without its leading underscore, and the
``homes``/``identity``/``vocabulary`` trio that used to be passed separately
everywhere is now the single ``Axes`` value they always travelled as.
"""

from __future__ import annotations

from collections.abc import Hashable, Mapping
from dataclasses import dataclass, field
from typing import Any

if __package__:
    from .mill_reviewed_vocabulary import (
        REVIEWED_GOAL_STRONG_ANCHORS,
        REVIEWED_GOAL_TOKEN_HOMES,
    )
else:
    from mill_reviewed_vocabulary import (
        REVIEWED_GOAL_STRONG_ANCHORS,
        REVIEWED_GOAL_TOKEN_HOMES,
    )

# A goal token has to recur inside a destination before it counts as that
# destination's vocabulary; one record cannot vouch for itself.
GOAL_FAMILY_MIN_SUPPORT = 2
# The goal-family axis fires only on a clean split: nothing shared with the
# destination, and a single other destination that shares at least this many
# tokens. Below that, a short or unusual goal is not evidence of a foreign mill.
GOAL_FAMILY_MIN_FOREIGN_TOKENS = 3


@dataclass(frozen=True)
class Entry:
    """One indexed record, reduced to the signals ownership resolution reads."""

    factory: str
    factory_verified: bool
    ref: Hashable
    record_id: str | None
    mill_prefix: str | None
    declared_factory: str | None
    goal_family: frozenset[str] = field(default_factory=frozenset)
    # Every claim the payload makes, including a preference wrapper's sides.
    # ``declared_factory`` is the agreed one and stays None when they clash;
    # the foreignness checks read the claims so a clash is still reported.
    declared_claims: tuple[str, ...] = ()


@dataclass(frozen=True)
class Axes:
    """The resolved per-run picture an entry's signals are judged against.

    These three maps are built in order -- identity, then prefix homes, then
    goal vocabulary -- and from then on always travel together, so they are
    one value rather than three parallel arguments. ``vocabulary`` is empty
    while the earlier phases are still resolving it.
    """

    identity: Mapping[str, str | None]
    homes: Mapping[str, frozenset[str]]
    vocabulary: Mapping[str, frozenset[str]] = field(default_factory=dict)


def reported_declaration(entry: Entry, expected: str | None) -> str | None:
    """Return the declaration to name on one finding.

    The agreed claim when the payload makes exactly one; otherwise the first
    claim that disagrees with the destination, so a self-contradictory record
    still names the foreign factory it attests instead of reporting nothing.
    """

    if entry.declared_factory is not None:
        return entry.declared_factory
    return next(
        (claim for claim in entry.declared_claims if claim != expected), None
    )


def entry_label(entry: Entry) -> str:
    """Return the stable label used to record one entry in a result set.

    The record's own id when present, else its ref stringified, else a fixed
    placeholder. A ref is an opaque token the caller chose to address its own
    records by -- census passes ``(relative path, line number)``, curation
    passes a decision index -- so its type is genuinely ``Any`` here, and
    stringifying it is the whole point rather than an accident.
    """

    ref: Any = entry.ref
    return entry.record_id or (str(ref) if ref is not None else "<unknown>")


def _payload_disagrees(entry: Entry, expected: str | None) -> bool:
    """True when any claim this payload makes names another resolved factory."""

    return expected is not None and any(
        claim != expected for claim in entry.declared_claims
    )


def _prefix_disagrees(
    entry: Entry, prefix_homes: frozenset[str], effective_factory: str
):
    """True when this record id's prefix has a resolved home excluding this one.

    An empty home set means the prefix is unresolved, not foreign, and is
    deliberately returned as-is rather than coerced to ``False``.
    """

    return (
        entry.mill_prefix is not None
        and prefix_homes
        and effective_factory not in prefix_homes
    )


def foreignness(entry: Entry, axes: Axes) -> tuple[bool, bool, str]:
    """Return (payload_foreign, prefix_foreign, effective_factory).

    The pair of checks repeated at every place these modules ask whether one
    entry's own evidence disagrees with its destination: a payload declaration
    that names a different resolved factory, and a mill id prefix whose
    resolved home excludes this one.
    """

    expected = axes.identity.get(entry.factory)
    effective_factory = expected or entry.factory
    prefix_homes = axes.homes.get(entry.mill_prefix, frozenset())
    return (
        _payload_disagrees(entry, expected),
        _prefix_disagrees(entry, prefix_homes, effective_factory),
        effective_factory,
    )


def _has_native_strong_anchor(entry: Entry, effective_factory: str) -> bool:
    """True when a reviewed strong anchor in this goal names this destination."""

    return any(
        token in REVIEWED_GOAL_STRONG_ANCHORS
        and REVIEWED_GOAL_TOKEN_HOMES.get(token) == effective_factory
        for token in entry.goal_family
    )


def is_novel_unreviewed_goal(
    entry: Entry,
    effective_factory: str,
    reviewed_goal_tokens: frozenset[str],
) -> bool:
    """True when a goal's unreviewed vocabulary is large with no native anchor.

    A goal family with at least ``GOAL_FAMILY_MIN_FOREIGN_TOKENS`` tokens
    outside the reviewed vocabulary, and no reviewed strong-anchor token that
    names this destination, is too novel to resolve.
    """

    unknown_score = len(entry.goal_family - reviewed_goal_tokens)
    if unknown_score < GOAL_FAMILY_MIN_FOREIGN_TOKENS:
        return False
    return not _has_native_strong_anchor(entry, effective_factory)


def _foreign_scores(
    entry: Entry,
    vocabulary: Mapping[str, frozenset[str]],
    own_factory: str,
) -> list[tuple[int, str]]:
    """Score this goal against every destination but its own, best first."""

    return sorted(
        (
            (len(entry.goal_family & tokens), other_factory)
            for other_factory, tokens in vocabulary.items()
            if other_factory != own_factory
        ),
        reverse=True,
    )


def _is_clear_winner(scored: list[tuple[int, str]], own_score: int) -> bool:
    """True when the top score wins outright.

    It must clear ``GOAL_FAMILY_MIN_FOREIGN_TOKENS``, beat what the goal
    shares with its own destination, and have no runner-up tied with it.
    """

    best_score = scored[0][0]
    if best_score < GOAL_FAMILY_MIN_FOREIGN_TOKENS:
        return False
    if best_score <= own_score:
        return False
    return not (len(scored) > 1 and scored[1][0] == best_score)


def _dominant_foreign_factory(
    entry: Entry,
    vocabulary: Mapping[str, frozenset[str]],
    own_factory: str,
) -> str | None:
    """Return the single other destination this goal scores highest against."""

    scored = _foreign_scores(entry, vocabulary, own_factory)
    if not scored:
        return None
    own = vocabulary.get(own_factory, frozenset())
    own_score = len(entry.goal_family & own)
    return scored[0][1] if _is_clear_winner(scored, own_score) else None


def _has_independent_anchor(best_tokens: frozenset[str]) -> bool:
    """True when a foreign goal match rests on more than generic reviewed terms.

    Reviewed generic terms such as retry/backoff/jitter are useful only when
    the same goal also carries a strong reviewed anchor for that home. A goal
    may alternatively rely on corpus-derived unique tokens. Without either
    form of independent evidence, repeated native records can be falsely
    quarantined merely for using common operational words.
    """

    if best_tokens & REVIEWED_GOAL_STRONG_ANCHORS:
        return True
    return bool(best_tokens - frozenset(REVIEWED_GOAL_TOKEN_HOMES))


def raw_goal_family_home(
    entry: Entry,
    vocabulary: Mapping[str, frozenset[str]],
    factory: str | None = None,
    *,
    require_independent_anchor: bool = True,
) -> str | None:
    """Return the one other destination this goal clearly belongs to."""

    if not entry.goal_family:
        return None
    own_factory = factory or entry.factory
    best_factory = _dominant_foreign_factory(entry, vocabulary, own_factory)
    if best_factory is None:
        return None
    if not require_independent_anchor:
        return best_factory
    best_tokens = entry.goal_family & vocabulary[best_factory]
    return best_factory if _has_independent_anchor(best_tokens) else None
