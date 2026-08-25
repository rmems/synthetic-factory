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
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Hashable, Iterable, Mapping

# ``<mill>-r<round>[<suffix>]-<slug>``: the id shape every agentic factory
# emits. ``r4_29``-style round tokens occur in a handful of published rounds
# and are accepted. An id that does not carry a round token has no mill prefix
# we are willing to guess at, and contributes no id-prefix evidence.
MILL_ID_RE = re.compile(r"^(?P<prefix>[a-z][a-z0-9]{1,7})-r[0-9][0-9_]*[a-z]*(?:-|$)")
GOAL_TOKEN_RE = re.compile(r"[a-z][a-z0-9]{2,}")

REASON_FOREIGN_PAYLOAD_FACTORY = "FOREIGN_PAYLOAD_FACTORY"
REASON_FOREIGN_MILL_ID_PREFIX = "FOREIGN_MILL_ID_PREFIX"
REASON_FOREIGN_MILL_GOAL_FAMILY = "FOREIGN_MILL_GOAL_FAMILY"

REASON_CODES = (
    REASON_FOREIGN_PAYLOAD_FACTORY,
    REASON_FOREIGN_MILL_ID_PREFIX,
    REASON_FOREIGN_MILL_GOAL_FAMILY,
)

# A goal token has to recur inside a destination before it counts as that
# destination's vocabulary; one record cannot vouch for itself.
GOAL_FAMILY_MIN_SUPPORT = 2
# The goal-family axis fires only on a clean split: nothing shared with the
# destination, and a single other destination that shares at least this many
# tokens. Below that, a short or unusual goal is not evidence of a foreign mill.
GOAL_FAMILY_MIN_FOREIGN_TOKENS = 3

# Vocabulary shared by every lane in this corpus: the leftover mechanic itself,
# the fix/verify arc, and episode scaffolding nouns. These words say nothing
# about which mill wrote a goal, so they are excluded from the goal family.
GOAL_STOPWORDS = frozenset(
    """
    add added adds after also and are was were been before but can case cases
    check checked checks correct correcting corrects dont drop dropped dropping
    drops during ensure ensuring error errors fail failed failing fails failure
    fix fixed fixes fixing for from full goal goals had has have here how into
    issue issues its keep keeping keeps key keys lattice leftover leftovers must
    name names new not old onto over partial pass passed passes path paths plant
    plants remove removed removes removing repair repaired repairs repairing
    reset resets run runs set sets should stale state states step steps than
    that the their then there these this those under until use used uses using
    valid validate value values verify verified verifies verifying was when
    while with without
    """.split()
)


def record_id(record: Any) -> str | None:
    """Return the record's own id, falling back to ``meta.id``."""

    if not isinstance(record, Mapping):
        return None
    for container in (record, record.get("meta")):
        if not isinstance(container, Mapping):
            continue
        value = container.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def mill_prefix(record: Any) -> str | None:
    """Return the mill id prefix carried by a record id, or ``None``."""

    identifier = record_id(record)
    if identifier is None:
        return None
    match = MILL_ID_RE.match(identifier)
    return match.group("prefix") if match else None


def declared_factory(record: Any) -> str | None:
    """Return the factory the payload claims for itself."""

    if not isinstance(record, Mapping):
        return None
    meta = record.get("meta")
    if not isinstance(meta, Mapping):
        return None
    value = meta.get("factory")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def goal_text(record: Any) -> str | None:
    """Return the task goal, including the per-side goals of a preference pair."""

    if not isinstance(record, Mapping):
        return None
    parts: list[str] = []
    for container in (record, record.get("chosen"), record.get("rejected")):
        if not isinstance(container, Mapping):
            continue
        value = container.get("goal")
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    return " ".join(parts) if parts else None


def goal_family(record: Any) -> frozenset[str]:
    """Return the mill-identifying content tokens of a record's goal."""

    text = goal_text(record)
    if text is None:
        return frozenset()
    return frozenset(
        token
        for token in GOAL_TOKEN_RE.findall(text.lower())
        if token not in GOAL_STOPWORDS
    )


@dataclass(frozen=True)
class MillFinding:
    """One record whose mill signals disagree with the directory it sits in."""

    factory: str
    ref: Hashable
    record_id: str | None
    reason_codes: tuple[str, ...]
    mill_prefix: str | None = None
    declared_factory: str | None = None
    expected_factory: str | None = None
    home_factories: tuple[str, ...] = ()
    goal_family_home: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "factory": self.factory,
            "record_id": self.record_id,
            "reason_codes": list(self.reason_codes),
        }
        if self.mill_prefix is not None:
            payload["mill_prefix"] = self.mill_prefix
        if self.declared_factory is not None:
            payload["declared_factory"] = self.declared_factory
        if self.expected_factory is not None:
            payload["expected_factory"] = self.expected_factory
        if self.home_factories:
            payload["home_factories"] = list(self.home_factories)
        if self.goal_family_home is not None:
            payload["goal_family_home"] = self.goal_family_home
        return payload


@dataclass(frozen=True)
class _Entry:
    factory: str
    factory_verified: bool
    ref: Hashable
    record_id: str | None
    mill_prefix: str | None
    declared_factory: str | None
    goal_family: frozenset[str] = field(default_factory=frozenset)


class MillIndex:
    """Accumulate records per destination, then resolve mill ownership.

    Ownership is resolved from the corpus rather than from a hand-maintained
    table, so a new lane needs no registration.  Every axis resolves ties by
    reporting nothing: a signal that does not clearly belong somewhere else is
    not evidence that it is foreign here.
    """

    def __init__(self) -> None:
        self._entries: list[_Entry] = []

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
            _Entry(
                factory=str(factory),
                factory_verified=bool(factory_verified),
                ref=ref,
                record_id=record_id(record),
                mill_prefix=mill_prefix(record),
                declared_factory=declared_factory(record),
                goal_family=goal_family(record),
            )
        )

    # -- resolution ---------------------------------------------------

    def _prefix_homes(
        self, identity: Mapping[str, str | None] | None = None
    ) -> dict[str, frozenset[str]]:
        """Map prefixes to homes supported by independent evidence.

        A maximum share is not ownership: one rare native alias can have a
        lower within-factory share than one spill in a smaller destination.
        Prefer one consistent payload declaration.  Otherwise, a prefix seen
        in several factories resolves only when exactly one factory is pure
        for that prefix.  Ambiguous aliases intentionally have no home and
        therefore cannot quarantine either side.
        """

        counts: dict[str, Counter[str]] = defaultdict(Counter)
        totals: Counter[str] = Counter()
        declarations: dict[str, set[str]] = defaultdict(set)
        for entry in self._entries:
            if entry.mill_prefix is not None:
                factory = (
                    identity.get(entry.factory) if identity is not None else None
                ) or entry.factory
                counts[entry.mill_prefix][factory] += 1
                totals[factory] += 1
                if entry.declared_factory is not None:
                    declarations[entry.mill_prefix].add(entry.declared_factory)
        homes: dict[str, frozenset[str]] = {}
        for prefix, per_factory in counts.items():
            declared = declarations[prefix]
            if len(declared) == 1:
                homes[prefix] = frozenset(declared)
                continue
            if len(per_factory) == 1:
                homes[prefix] = frozenset(per_factory)
                continue
            pure = {
                factory
                for factory, seen in per_factory.items()
                if seen == totals[factory]
            }
            homes[prefix] = frozenset(pure) if len(pure) == 1 else frozenset()
        return homes

    def _declared_identity(self) -> dict[str, str | None]:
        """Map each destination to the single factory its payloads declare.

        Compared against the payloads rather than the directory name so that
        the check holds for snapshots, staging copies, and fixtures whose
        directory is not named after a factory slug.
        """

        verified = {
            entry.factory for entry in self._entries if entry.factory_verified
        }
        counts: dict[str, Counter[str]] = defaultdict(Counter)
        for entry in self._entries:
            if entry.declared_factory is not None:
                counts[entry.factory][entry.declared_factory] += 1
        identity: dict[str, str | None] = {
            factory: factory for factory in verified
        }
        for factory, per_declared in counts.items():
            if factory in verified:
                continue
            # A declaration matching the enclosing factory is independent
            # native evidence. Prefer it over a majority that may consist of
            # foreign or otherwise poisoned records. Snapshot/off-slug roots
            # fall back to the unique most common declaration below.
            if factory in per_declared:
                identity[factory] = factory
                continue
            top = max(per_declared.values())
            winners = [name for name, seen in per_declared.items() if seen == top]
            identity[factory] = winners[0] if len(winners) == 1 else None
        return identity

    def ownership_context(self) -> dict[str, Any]:
        """Describe whether cross-factory ownership is safe for output.

        Curation may report an incomplete source, but it must not write a
        cleaned tree when a cross-factory prefix is ambiguous or when a signal
        names a home factory absent from the verified source context.
        """

        verified = {
            entry.factory for entry in self._entries if entry.factory_verified
        }
        prefix_factories: dict[str, set[str]] = defaultdict(set)
        for entry in self._entries:
            if entry.mill_prefix is not None:
                prefix_factories[entry.mill_prefix].add(entry.factory)

        identity = self._declared_identity()
        homes = self._prefix_homes(identity)
        unresolved_prefixes = sorted(
            prefix
            for prefix, factories in prefix_factories.items()
            if len(factories) > 1 and not homes.get(prefix)
        )
        missing_homes = {
            home
            for prefix_homes in homes.values()
            for home in prefix_homes
            if home not in verified
        }
        missing_homes.update(
            entry.declared_factory
            for entry in self._entries
            if entry.factory_verified
            and entry.declared_factory is not None
            and entry.declared_factory != entry.factory
            and entry.declared_factory not in verified
        )
        missing_homes.discard(None)
        complete = (
            len(verified) >= 2
            and not unresolved_prefixes
            and not missing_homes
        )
        return {
            "complete": complete,
            "verified_factories": sorted(verified),
            "unresolved_prefixes": unresolved_prefixes,
            "missing_home_factories": sorted(missing_homes),
        }

    def _goal_vocabulary(
        self,
        homes: Mapping[str, frozenset[str]],
        identity: Mapping[str, str | None],
    ) -> dict[str, frozenset[str]]:
        """Map each destination to goal tokens uniquely characteristic of it.

        A repeated stray must not teach the destination its foreign vocabulary.
        Token ownership therefore uses within-destination prevalence, not just
        a minimum raw count. Prefix- or payload-foreign records are excluded
        from the teaching set entirely, and tied tokens are non-discriminating.
        """

        counts: dict[str, Counter[str]] = defaultdict(Counter)
        totals: Counter[str] = Counter()
        for entry in self._entries:
            prefix = entry.mill_prefix
            expected = identity.get(entry.factory)
            factory = expected or entry.factory
            if prefix is not None and factory not in homes.get(prefix, ()):
                # A record already known to come from elsewhere must not teach
                # this destination its vocabulary.
                continue
            if (
                entry.declared_factory is not None
                and expected is not None
                and entry.declared_factory != expected
            ):
                continue
            totals[factory] += 1
            for token in entry.goal_family:
                counts[token][factory] += 1

        vocabulary: dict[str, set[str]] = defaultdict(set)
        for token, per_factory in counts.items():
            supported = {
                factory: seen
                for factory, seen in per_factory.items()
                if seen >= GOAL_FAMILY_MIN_SUPPORT
            }
            if not supported:
                continue
            prevalence = {
                factory: Fraction(seen, totals[factory])
                for factory, seen in supported.items()
                if totals[factory]
            }
            if not prevalence:
                continue
            top = max(prevalence.values())
            winners = [
                factory for factory, share in prevalence.items() if share == top
            ]
            if len(winners) == 1:
                vocabulary[winners[0]].add(token)
        return {
            factory: frozenset(tokens)
            for factory, tokens in vocabulary.items()
        }

    def _goal_family_home(
        self,
        entry: _Entry,
        vocabulary: Mapping[str, frozenset[str]],
        factory: str | None = None,
    ) -> str | None:
        """Return the one other destination this goal clearly belongs to."""

        own_factory = factory or entry.factory
        own = vocabulary.get(own_factory, frozenset())
        if not own or not entry.goal_family:
            return None
        own_score = len(entry.goal_family & own)
        scored = sorted(
            (
                (len(entry.goal_family & tokens), factory)
                for factory, tokens in vocabulary.items()
                if factory != own_factory
            ),
            reverse=True,
        )
        if not scored:
            return None
        best_score, best_factory = scored[0]
        if best_score < GOAL_FAMILY_MIN_FOREIGN_TOKENS:
            return None
        if best_score <= own_score:
            return None
        if len(scored) > 1 and scored[1][0] == best_score:
            return None
        return best_factory

    def findings(self) -> tuple[MillFinding, ...]:
        """Return every indexed record whose mill signals are foreign, in order."""

        identity = self._declared_identity()
        homes = self._prefix_homes(identity)
        vocabulary = self._goal_vocabulary(homes, identity)

        results: list[MillFinding] = []
        for entry in self._entries:
            reasons: list[str] = []
            expected = identity.get(entry.factory)
            effective_factory = expected or entry.factory
            if (
                entry.declared_factory is not None
                and expected is not None
                and entry.declared_factory != expected
            ):
                reasons.append(REASON_FOREIGN_PAYLOAD_FACTORY)

            prefix_homes = homes.get(entry.mill_prefix, frozenset())
            if (
                entry.mill_prefix is not None
                and prefix_homes
                and effective_factory not in prefix_homes
            ):
                reasons.append(REASON_FOREIGN_MILL_ID_PREFIX)

            goal_home = self._goal_family_home(
                entry, vocabulary, effective_factory
            )
            if goal_home is not None:
                reasons.append(REASON_FOREIGN_MILL_GOAL_FAMILY)

            if not reasons:
                continue
            results.append(
                MillFinding(
                    factory=entry.factory,
                    ref=entry.ref,
                    record_id=entry.record_id,
                    reason_codes=tuple(reasons),
                    mill_prefix=entry.mill_prefix,
                    declared_factory=entry.declared_factory,
                    expected_factory=(
                        expected
                        if REASON_FOREIGN_PAYLOAD_FACTORY in reasons
                        else None
                    ),
                    home_factories=(
                        tuple(sorted(prefix_homes))
                        if REASON_FOREIGN_MILL_ID_PREFIX in reasons
                        else ()
                    ),
                    goal_family_home=goal_home,
                )
            )
        return tuple(results)


def summarize(findings: Iterable[MillFinding], id_limit: int = 200) -> dict[str, Any]:
    """Build the JSON-safe mill-mix block shared by census and curation."""

    findings = tuple(findings)
    reason_counts: Counter[str] = Counter()
    by_factory: dict[str, dict[str, Any]] = {}
    for finding in findings:
        reason_counts.update(finding.reason_codes)
        bucket = by_factory.setdefault(
            finding.factory, {"records": 0, "foreign_prefixes": Counter()}
        )
        bucket["records"] += 1
        if REASON_FOREIGN_MILL_ID_PREFIX in finding.reason_codes:
            bucket["foreign_prefixes"][finding.mill_prefix] += 1

    identifiers = sorted(
        finding.record_id for finding in findings if finding.record_id is not None
    )
    return {
        "records": len(findings),
        "reason_codes": dict(sorted(reason_counts.items())),
        "by_factory": {
            factory: {
                "records": bucket["records"],
                "foreign_prefixes": dict(sorted(bucket["foreign_prefixes"].items())),
            }
            for factory, bucket in sorted(by_factory.items())
        },
        "record_ids": identifiers[:id_limit],
        "record_ids_truncated": len(identifiers) > id_limit,
    }
