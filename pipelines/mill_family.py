#!/usr/bin/env python3
"""Detect leftover-mill records that were published into a foreign factory.

A "mill" is one generator lane. Its records share three observable signals:

* the **payload factory** they declare (``meta.factory``),
* the **mill id prefix** their record id carries (``gql-r1405-...`` -> ``gql``),
* the **goal family** their task goal is written from (its content vocabulary).

Mill mix is when a record carrying one mill's signals is published inside a
different mill's directory.  This module resolves those three axes across a
whole run and reports every disagreement.

Two anti-patterns are deliberately avoided, because published mixes have been
observed that defeat both:

* The literal token ``leftover`` in a record id is **not** the mill test.  Every
  lane in this corpus generates leftover-mechanic tasks, and a foreign record
  whose id happens to omit the word is still foreign.
* The absence of a destination-specific field (``diagnosis``,
  ``error_introduced``, ...) is **not** the mill test.  Generic episode slugs
  have no such field to miss, so a dest-field-absence check is blind there.

Nothing here reads or writes a corpus tree: callers feed decoded records in and
get findings back.  See ``census.py`` (reporting) and ``curate_agentic.py``
(quarantine) for the two in-tree callers.

This module is the stable entry point and the accumulator.  The resolution it
drives lives in four siblings, each named for one responsibility:

* ``mill_signals.py`` -- what one record says about itself.
* ``mill_locations.py`` -- which factory directory a path belongs to.
* ``mill_evidence.py`` -- whether one entry's signals disagree with its home.
* ``mill_resolution.py`` -- the per-run identity/prefix/vocabulary maps.
* ``mill_ownership.py`` -- sequencing those into an export-safety verdict.
* ``mill_findings.py`` -- how a disagreement is reported.

Every public name any of them defines is re-exported here, so existing
``from mill_family import ...`` call sites resolve exactly as before.
"""

from __future__ import annotations

from collections.abc import Hashable, Mapping
from typing import Any

if __package__:
    from .mill_evidence import (
        GOAL_FAMILY_MIN_FOREIGN_TOKENS,
        GOAL_FAMILY_MIN_SUPPORT,
        Axes,
        Entry,
        foreignness,
        reported_declaration,
    )
    from .mill_findings import (
        REASON_CODES,
        REASON_FOREIGN_MILL_GOAL_FAMILY,
        REASON_FOREIGN_MILL_ID_PREFIX,
        REASON_FOREIGN_PAYLOAD_FACTORY,
        MillFinding,
        summarize,
    )
    from .mill_locations import factory_identity_for_path
    from .mill_ownership import ownership_context as _ownership_context
    from .mill_resolution import (
        count_goal_tokens,
        declared_identity,
        goal_family_homes,
        goal_vocabulary,
        prefix_homes,
    )
    from .mill_reviewed_vocabulary import (
        REVIEWED_GOAL_STRONG_ANCHORS,
        REVIEWED_GOAL_TOKEN_HOMES,
        REVIEWED_MILL_PREFIX_HOMES,
    )
    from .mill_signals import (
        GOAL_STOPWORDS,
        GOAL_TOKEN_RE,
        MILL_ID_RE,
        declared_factory,
        declared_factory_claims,
        goal_family,
        goal_text,
        mill_prefix,
        record_id,
    )
else:
    from mill_evidence import (
        GOAL_FAMILY_MIN_FOREIGN_TOKENS,
        GOAL_FAMILY_MIN_SUPPORT,
        Axes,
        Entry,
        foreignness,
        reported_declaration,
    )
    from mill_findings import (
        REASON_CODES,
        REASON_FOREIGN_MILL_GOAL_FAMILY,
        REASON_FOREIGN_MILL_ID_PREFIX,
        REASON_FOREIGN_PAYLOAD_FACTORY,
        MillFinding,
        summarize,
    )
    from mill_locations import factory_identity_for_path
    from mill_ownership import ownership_context as _ownership_context
    from mill_resolution import (
        count_goal_tokens,
        declared_identity,
        goal_family_homes,
        goal_vocabulary,
        prefix_homes,
    )
    from mill_reviewed_vocabulary import (
        REVIEWED_GOAL_STRONG_ANCHORS,
        REVIEWED_GOAL_TOKEN_HOMES,
        REVIEWED_MILL_PREFIX_HOMES,
    )
    from mill_signals import (
        GOAL_STOPWORDS,
        GOAL_TOKEN_RE,
        MILL_ID_RE,
        declared_factory,
        declared_factory_claims,
        goal_family,
        goal_text,
        mill_prefix,
        record_id,
    )

# The full public surface of this module, re-exported from the siblings above.
# Every name here was importable from ``mill_family`` before the split and
# must stay importable from it.
__all__ = [
    "GOAL_FAMILY_MIN_FOREIGN_TOKENS",
    "GOAL_FAMILY_MIN_SUPPORT",
    "GOAL_STOPWORDS",
    "GOAL_TOKEN_RE",
    "MILL_ID_RE",
    "REASON_CODES",
    "REASON_FOREIGN_MILL_GOAL_FAMILY",
    "REASON_FOREIGN_MILL_ID_PREFIX",
    "REASON_FOREIGN_PAYLOAD_FACTORY",
    "REVIEWED_GOAL_STRONG_ANCHORS",
    "REVIEWED_GOAL_TOKEN_HOMES",
    "REVIEWED_MILL_PREFIX_HOMES",
    "MillFinding",
    "MillIndex",
    "declared_factory",
    "declared_factory_claims",
    "factory_identity_for_path",
    "goal_family",
    "goal_text",
    "mill_prefix",
    "record_id",
    "summarize",
]


def _entry_reasons(
    entry: Entry,
    axes: Axes,
    goal_homes: Mapping[Entry, str],
) -> list[str]:
    """Return the reason codes one entry fires, in axis order."""

    payload_foreign, prefix_foreign, _ = foreignness(entry, axes)
    reasons: list[str] = []
    if payload_foreign:
        reasons.append(REASON_FOREIGN_PAYLOAD_FACTORY)
    if prefix_foreign:
        reasons.append(REASON_FOREIGN_MILL_ID_PREFIX)
    if goal_homes.get(entry) is not None:
        reasons.append(REASON_FOREIGN_MILL_GOAL_FAMILY)
    return reasons


class MillIndex:
    """Accumulate records per destination, then resolve mill ownership.

    Reviewed aliases are resolved from independent registry evidence. Unknown
    signals are inferred only when corpus evidence is unambiguous; conflicting
    declarations or cross-factory goal vocabularies remain unresolved. A
    signal that does not clearly belong somewhere else is never evidence that
    it is foreign here.
    """

    def __init__(self) -> None:
        self._entries: list[Entry] = []

    def __len__(self) -> int:
        return len(self._entries)

    def add(
        self,
        factory: str,
        record: Any,
        ref: Hashable = None,
        *,
        factory_verified: bool = False,
    ) -> None:
        """Index one record plus independent directory-identity evidence.

        ``factory_verified`` means the caller resolved ``factory`` from a
        registered, marker-backed, or directly invoked factory root.  An
        off-slug snapshot label is deliberately unverified: its identity must
        still be inferred from payload evidence instead of from its name.
        """

        if not isinstance(record, Mapping):
            return
        self._entries.append(
            Entry(
                factory=str(factory),
                factory_verified=bool(factory_verified),
                ref=ref,
                record_id=record_id(record),
                mill_prefix=mill_prefix(record),
                declared_factory=declared_factory(record),
                goal_family=goal_family(record),
                declared_claims=declared_factory_claims(record),
            )
        )

    # -- resolution ---------------------------------------------------
    #
    # Thin delegations to ``mill_resolution``/``mill_ownership``. They stay
    # methods because callers and tests reach them through an index instance.

    def _declared_identity(self) -> dict[str, str | None]:
        """Map each destination to the single factory its payloads declare."""

        return declared_identity(self._entries)

    def _prefix_homes(
        self, identity: Mapping[str, str | None] | None = None
    ) -> dict[str, frozenset[str]]:
        """Map prefixes to homes supported by independent evidence."""

        return prefix_homes(self._entries, identity)

    def _goal_token_counts(
        self,
        homes: Mapping[str, frozenset[str]],
        identity: Mapping[str, str | None],
    ) -> dict[str, Any]:
        """Count goal tokens using only records not known to be foreign."""

        return count_goal_tokens(
            self._entries, Axes(identity=identity, homes=homes)
        )

    def _goal_vocabulary(
        self,
        homes: Mapping[str, frozenset[str]],
        identity: Mapping[str, str | None],
        *,
        goal_token_counts: Mapping[str, Any] | None = None,
    ) -> dict[str, frozenset[str]]:
        """Map each destination to goal tokens uniquely characteristic of it."""

        return goal_vocabulary(
            self._entries,
            Axes(identity=identity, homes=homes),
            goal_token_counts=goal_token_counts,
        )

    def _goal_family_homes(
        self,
        vocabulary: Mapping[str, frozenset[str]],
        homes: Mapping[str, frozenset[str]],
        identity: Mapping[str, str | None],
    ) -> dict[Entry, str]:
        """Return supported foreign goal homes without convicting one overlap."""

        return goal_family_homes(
            self._entries,
            Axes(identity=identity, homes=homes, vocabulary=vocabulary),
        )

    def ownership_context(self) -> dict[str, Any]:
        """Describe whether cross-factory ownership is safe for output."""

        return _ownership_context(self._entries)

    # -- reporting ----------------------------------------------------

    def findings(self) -> tuple[MillFinding, ...]:
        """Return every indexed record whose mill signals are foreign, in order."""

        identity = self._declared_identity()
        homes = self._prefix_homes(identity)
        vocabulary = self._goal_vocabulary(homes, identity)
        axes = Axes(identity=identity, homes=homes, vocabulary=vocabulary)
        goal_homes = self._goal_family_homes(vocabulary, homes, identity)

        results: list[MillFinding] = []
        for entry in self._entries:
            reasons = _entry_reasons(entry, axes, goal_homes)
            if not reasons:
                continue
            expected = identity.get(entry.factory)
            prefix_homes_for_entry = homes.get(entry.mill_prefix, frozenset())
            results.append(
                MillFinding(
                    factory=entry.factory,
                    ref=entry.ref,
                    record_id=entry.record_id,
                    reason_codes=tuple(reasons),
                    mill_prefix=entry.mill_prefix,
                    declared_factory=reported_declaration(entry, expected),
                    expected_factory=(
                        expected
                        if REASON_FOREIGN_PAYLOAD_FACTORY in reasons
                        else None
                    ),
                    home_factories=(
                        tuple(sorted(prefix_homes_for_entry))
                        if REASON_FOREIGN_MILL_ID_PREFIX in reasons
                        else ()
                    ),
                    goal_family_home=goal_homes.get(entry),
                )
            )
        return tuple(results)
