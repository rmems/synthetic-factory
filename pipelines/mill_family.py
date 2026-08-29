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
from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mill_reviewed_vocabulary import (
    REVIEWED_GOAL_STRONG_ANCHORS,
    REVIEWED_GOAL_TOKEN_HOMES,
    REVIEWED_MILL_PREFIX_HOMES,
)

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
# REVIEWED_MILL_PREFIX_HOMES, REVIEWED_GOAL_TOKEN_HOMES, and
# REVIEWED_GOAL_STRONG_ANCHORS live in mill_reviewed_vocabulary.py and are
# imported above; see that module's docstring for what each one pins.


def factory_identity_for_path(
    run_dir: Path,
    path: Path,
    *,
    marker_root: Path | None = None,
    known_factories: Iterable[str] = (),
) -> tuple[str, bool]:
    """Return one shared factory identity and independent verification flag.

    Marker-mode roots are verified directly. A known outer factory root is
    also verified, while off-registry direct roots and standalone files remain
    unverified. Multi-factory runs attribute nested archive/work paths to the
    first enclosing factory-shaped component.
    """

    run_dir = Path(run_dir)
    path = Path(path)
    if marker_root is not None:
        return Path(marker_root).name, True
    if run_dir.is_file():
        return path.parent.name, False

    factories = frozenset(known_factories)
    relative = path.relative_to(run_dir)
    if run_dir.name in factories:
        return run_dir.name, True
    if run_dir.name.endswith("-factory"):
        if len(relative.parts) == 1:
            return run_dir.name, False
        nested_root = relative.parts[0]
        if nested_root not in factories and not nested_root.endswith("-factory"):
            return run_dir.name, False
    factory = relative.parts[0] if len(relative.parts) > 1 else run_dir.name
    return factory, factory in factories

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


def _entry_label(entry: _Entry) -> str:
    """Return the stable label used to record one entry in a result set.

    Verbatim extraction of the expression this replaces: the record's own
    id when present, else its ref stringified, else a fixed placeholder.
    """

    return entry.record_id or (
        str(entry.ref) if entry.ref is not None else "<unknown>"
    )


@dataclass(frozen=True)
class _OwnershipResolutionContext:
    """Read-only per-run context shared by every entry in one ownership pass.

    Bundles the values ``ownership_context`` resolves once before its
    per-entry loop, so the loop body can be a named helper (see
    ``MillIndex._resolve_entry_goal_ownership``) without an excess-argument
    call. Every field here is exactly one local ``ownership_context`` already
    computed; nothing is recomputed or reshaped.
    """

    identity: Mapping[str, str | None]
    homes: Mapping[str, frozenset[str]]
    vocabulary: Mapping[str, frozenset[str]]
    goal_homes: Mapping[_Entry, str]
    raw_goal_candidates: Mapping[_Entry, tuple[str, frozenset[str]]]
    raw_goal_candidate_support: Mapping[tuple[str, str, frozenset[str]], int]
    reference_scope_complete: bool
    ambiguous_goal_signatures: Mapping[_Entry, frozenset[str]]
    unresolved_ambiguous_signatures: frozenset[frozenset[str]]
    reviewed_goal_tokens: frozenset[str]
    verified: set[str]


@dataclass(frozen=True)
class _ResolvedAxes:
    """The three destination-resolution axes phases share before per-entry work.

    Bundles ``identity``/``homes``/``vocabulary`` so the collection helpers
    below take one context argument instead of three positional ones.
    """

    identity: Mapping[str, str | None]
    homes: Mapping[str, frozenset[str]]
    vocabulary: Mapping[str, frozenset[str]]


@dataclass(frozen=True)
class _AmbiguousSignatureAccumulator:
    """Mutable output pair for the ambiguous-goal-signature collection pass."""

    signatures: dict[_Entry, frozenset[str]]
    support: dict[frozenset[str], Counter[str]]


class MillIndex:
    """Accumulate records per destination, then resolve mill ownership.

    Reviewed aliases are resolved from independent registry evidence. Unknown
    signals are inferred only when corpus evidence is unambiguous; conflicting
    declarations or cross-factory goal vocabularies remain unresolved. A
    signal that does not clearly belong somewhere else is never evidence that
    it is foreign here.
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
        Prefer a reviewed alias or one consistent payload declaration. A
        prefix observed in only one factory is local. Conflicting declarations
        across factories intentionally have no inferred home; destination
        purity is not independent evidence and cannot resolve the conflict.
        """

        counts: dict[str, Counter[str]] = defaultdict(Counter)
        declarations: dict[str, set[str]] = defaultdict(set)
        for entry in self._entries:
            if entry.mill_prefix is None:
                continue
            factory = (
                identity.get(entry.factory) if identity is not None else None
            ) or entry.factory
            counts[entry.mill_prefix][factory] += 1
            if entry.declared_factory is not None:
                declarations[entry.mill_prefix].add(entry.declared_factory)
        return {
            prefix: self._resolve_prefix_home(
                prefix, per_factory, declarations[prefix]
            )
            for prefix, per_factory in counts.items()
        }

    @staticmethod
    def _resolve_prefix_home(
        prefix: str, per_factory: Counter[str], declared: set[str]
    ) -> frozenset[str]:
        """Return the resolved home(s) for one mill prefix.

        Extracted verbatim from the per-prefix branch in ``_prefix_homes``: a
        reviewed alias wins outright; otherwise one consistent payload
        declaration wins; otherwise a prefix seen under exactly one factory
        is local to it; otherwise the prefix has no inferred home.
        """

        reviewed_home = REVIEWED_MILL_PREFIX_HOMES.get(prefix)
        if reviewed_home is not None:
            return frozenset({reviewed_home})
        if len(declared) == 1:
            return frozenset(declared)
        if len(per_factory) == 1:
            return frozenset(per_factory)
        return frozenset()

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
            identity[factory] = self._resolve_unverified_identity(
                factory, per_declared
            )
        return identity

    @staticmethod
    def _resolve_unverified_identity(
        factory: str, per_declared: Counter[str]
    ) -> str | None:
        """Return the payload-declared identity for one unverified destination.

        Extracted verbatim from the per-factory branch in
        ``_declared_identity``. A declaration matching the directory's own
        name is independent native evidence, preferred over a majority that
        may consist of foreign or otherwise poisoned records. Snapshot/off-
        slug roots fall back to the unique most common declaration.
        """

        if factory in per_declared:
            return factory
        top = max(per_declared.values())
        winners = [name for name, seen in per_declared.items() if seen == top]
        return winners[0] if len(winners) == 1 else None

    @staticmethod
    def _foreignness(
        entry: _Entry,
        homes: Mapping[str, frozenset[str]],
        identity: Mapping[str, str | None],
    ) -> tuple[bool, bool, str]:
        """Return (payload_foreign, prefix_foreign, effective_factory).

        Verbatim extraction of the pair of checks repeated at every place
        this class asks whether one entry's own evidence disagrees with its
        destination: a payload declaration that names a different resolved
        factory, and a mill id prefix whose resolved home excludes this one.
        """

        expected = identity.get(entry.factory)
        effective_factory = expected or entry.factory
        prefix_homes = homes.get(entry.mill_prefix, frozenset())
        payload_foreign = (
            entry.declared_factory is not None
            and expected is not None
            and entry.declared_factory != expected
        )
        prefix_foreign = (
            entry.mill_prefix is not None
            and prefix_homes
            and effective_factory not in prefix_homes
        )
        return payload_foreign, prefix_foreign, effective_factory

    @staticmethod
    def _is_novel_unreviewed_goal(
        entry: _Entry,
        effective_factory: str,
        reviewed_goal_tokens: frozenset[str],
    ) -> bool:
        """True when a goal's unreviewed vocabulary is large with no native anchor.

        Verbatim extraction of the block this replaces: a goal family with at
        least ``GOAL_FAMILY_MIN_FOREIGN_TOKENS`` tokens outside the reviewed
        vocabulary, and no reviewed strong-anchor token that names this
        destination, is too novel to resolve.
        """

        has_native_strong_anchor = any(
            token in REVIEWED_GOAL_STRONG_ANCHORS
            and REVIEWED_GOAL_TOKEN_HOMES.get(token) == effective_factory
            for token in entry.goal_family
        )
        unknown_score = len(entry.goal_family - reviewed_goal_tokens)
        return (
            unknown_score >= GOAL_FAMILY_MIN_FOREIGN_TOKENS
            and not has_native_strong_anchor
        )

    def _resolve_entry_goal_ownership(
        self,
        entry: _Entry,
        context: _OwnershipResolutionContext,
        unresolved_goal_records: set[str],
        missing_homes: set[str | None],
    ) -> None:
        """Apply one entry's goal-ownership resolution, in place.

        Extracted verbatim from the per-entry pass in ``ownership_context``:
        same branches, same order, same early exits. Each ``continue`` in
        that loop becomes a ``return`` here, since returning from one
        per-entry call is exactly "move on to the next entry" -- the two are
        the same control flow, just expressed at a different call depth.
        """

        payload_foreign, prefix_foreign, effective_factory = self._foreignness(
            entry, context.homes, context.identity
        )
        if payload_foreign or prefix_foreign:
            return

        goal_home = context.goal_homes.get(entry)
        if goal_home is not None:
            if goal_home not in context.verified:
                missing_homes.add(goal_home)
            return

        raw_goal_candidate = context.raw_goal_candidates.get(entry)
        independently_anchored_candidate = self._raw_goal_family_home(
            entry, context.vocabulary, effective_factory
        )
        if (
            raw_goal_candidate is not None
            and independently_anchored_candidate is None
            and context.raw_goal_candidate_support[
                (
                    effective_factory,
                    raw_goal_candidate[0],
                    raw_goal_candidate[1],
                )
            ]
            >= GOAL_FAMILY_MIN_SUPPORT
        ):
            # Repeated generic reviewed terms are insufficient to
            # quarantine a record, but they are also not permission to
            # export it. Preserve that distinction by keeping the cohort
            # unresolved until stronger ownership evidence exists.
            unresolved_goal_records.add(_entry_label(entry))
            if raw_goal_candidate[0] not in context.verified:
                missing_homes.add(raw_goal_candidate[0])
            return

        if context.reference_scope_complete:
            # Full reviewed-prefix coverage does not resolve a novel goal
            # family repeated in multiple factories. Those tokens were
            # deliberately omitted from ``vocabulary`` as ambiguous; keep
            # their records unresolved instead of treating the omission as
            # permission to export them.
            if (
                context.ambiguous_goal_signatures.get(entry)
                in context.unresolved_ambiguous_signatures
            ):
                unresolved_goal_records.add(_entry_label(entry))
                return

            # Unique unreviewed vocabulary can self-teach one destination
            # and therefore appear native in ``vocabulary``. Covering every
            # reviewed prefix is not independent evidence for that novel
            # goal family, so keep it unresolved unless a reviewed native
            # product signature anchors the record.
            if self._is_novel_unreviewed_goal(
                entry, effective_factory, context.reviewed_goal_tokens
            ):
                unresolved_goal_records.add(_entry_label(entry))
            return

        # A singleton can resemble a reviewed foreign family while still
        # being a legitimate cross-domain task. Do not quarantine it on
        # that resemblance alone, but do fail a partial export closed: the
        # complete audited reference scope is what establishes that the
        # singleton is not part of a repeated foreign cohort.
        raw_goal_home = self._raw_goal_family_home(
            entry, context.vocabulary, effective_factory
        )
        if raw_goal_home is not None:
            unresolved_goal_records.add(_entry_label(entry))
            if raw_goal_home not in context.verified:
                missing_homes.add(raw_goal_home)
            return

        if self._is_novel_unreviewed_goal(
            entry, effective_factory, context.reviewed_goal_tokens
        ):
            unresolved_goal_records.add(_entry_label(entry))

    def _reference_scope_state(self) -> tuple[bool, dict[str, set[str]]]:
        """Return (reference_scope_complete, prefix_factories).

        Extracted verbatim from the setup block in ``ownership_context``:
        whether every reviewed prefix is covered by a verified entry naming
        its reviewed home, plus which factories each mill prefix was seen
        under.
        """

        reviewed_prefix_coverage = {
            (entry.mill_prefix, entry.factory)
            for entry in self._entries
            if entry.factory_verified
            and entry.mill_prefix is not None
            and REVIEWED_MILL_PREFIX_HOMES.get(entry.mill_prefix)
            == entry.factory
        }
        reference_scope_complete = all(
            (prefix, home) in reviewed_prefix_coverage
            for prefix, home in REVIEWED_MILL_PREFIX_HOMES.items()
        )
        prefix_factories: dict[str, set[str]] = defaultdict(set)
        for entry in self._entries:
            if entry.mill_prefix is not None:
                prefix_factories[entry.mill_prefix].add(entry.factory)
        return reference_scope_complete, prefix_factories

    @staticmethod
    def _unresolved_destinations(
        destinations: Iterable[str],
        identity: Mapping[str, str | None],
    ) -> list[str]:
        """Return destinations ``_declared_identity`` could not resolve.

        Extracted verbatim from the comprehension in ``ownership_context``.
        """

        return sorted(
            factory for factory in destinations if identity.get(factory) is None
        )

    def _collect_raw_goal_candidate(
        self,
        entry: _Entry,
        axes: _ResolvedAxes,
        raw_goal_candidates: dict[_Entry, tuple[str, frozenset[str]]],
        raw_goal_candidate_support: Counter[tuple[str, str, frozenset[str]]],
    ) -> None:
        """Record one entry's raw (unanchored) goal-family candidate, if any.

        Extracted verbatim from the per-entry pass that builds
        ``raw_goal_candidates``/``raw_goal_candidate_support`` in
        ``ownership_context``.
        """

        factory = axes.identity.get(entry.factory) or entry.factory
        candidate = self._raw_goal_family_home(
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
        payload_foreign, prefix_foreign, _ = self._foreignness(
            entry, axes.homes, axes.identity
        )
        if not payload_foreign and not prefix_foreign:
            raw_goal_candidate_support[
                (factory, candidate, candidate_signature)
            ] += 1

    @staticmethod
    def _unresolved_prefixes(
        prefix_factories: Mapping[str, set[str]],
        homes: Mapping[str, frozenset[str]],
    ) -> list[str]:
        """Return mill prefixes with no clean single-factory resolution.

        Extracted verbatim from the comprehension in ``ownership_context``: a
        prefix is unresolved when it is not a reviewed alias, or when it was
        seen under more than one factory and has no resolved home.
        """

        return sorted(
            prefix
            for prefix, factories in prefix_factories.items()
            if prefix not in REVIEWED_MILL_PREFIX_HOMES
            or (len(factories) > 1 and not homes.get(prefix))
        )

    def _missing_homes(
        self,
        homes: Mapping[str, frozenset[str]],
        identity: Mapping[str, str | None],
        verified: set[str],
    ) -> set[str | None]:
        """Return every home factory named by a signal but absent from ``verified``.

        Extracted verbatim from the three-part union in
        ``ownership_context``: prefix homes, resolved destination
        identities, and verified entries' own disagreeing declarations.
        """

        missing_homes = {
            home
            for prefix_homes in homes.values()
            for home in prefix_homes
            if home not in verified
        }
        missing_homes.update(
            expected
            for expected in identity.values()
            if expected is not None and expected not in verified
        )
        missing_homes.update(
            entry.declared_factory
            for entry in self._entries
            if entry.factory_verified
            and entry.declared_factory is not None
            and entry.declared_factory != entry.factory
            and entry.declared_factory not in verified
        )
        return missing_homes

    @staticmethod
    def _ambiguous_goal_tokens(
        goal_token_counts: Mapping[str, Counter[str]],
        reviewed_goal_tokens: frozenset[str],
    ) -> frozenset[str]:
        """Return goal tokens seen in 2+ factories with enough support to be ambiguous.

        Extracted verbatim from the comprehension in ``ownership_context``.
        """

        return frozenset(
            token
            for token, per_factory in goal_token_counts.items()
            if token not in reviewed_goal_tokens
            and len(per_factory) >= 2
            and any(
                seen >= GOAL_FAMILY_MIN_SUPPORT
                for seen in per_factory.values()
            )
        )

    def _collect_ambiguous_goal_signature(
        self,
        entry: _Entry,
        axes: _ResolvedAxes,
        ambiguous_goal_tokens: frozenset[str],
        accumulator: _AmbiguousSignatureAccumulator,
    ) -> None:
        """Record one entry's ambiguous-goal-token signature, if it has one.

        Extracted verbatim from the per-entry pass that builds
        ``ambiguous_goal_signatures``/``ambiguous_signature_support`` in
        ``ownership_context``.
        """

        payload_foreign, prefix_foreign, effective_factory = self._foreignness(
            entry, axes.homes, axes.identity
        )
        signature = frozenset(entry.goal_family & ambiguous_goal_tokens)
        if (
            payload_foreign
            or prefix_foreign
            or len(signature) < GOAL_FAMILY_MIN_FOREIGN_TOKENS
        ):
            return
        accumulator.signatures[entry] = signature
        accumulator.support[signature][effective_factory] += 1

    @staticmethod
    def _unresolved_ambiguous_signatures(
        ambiguous_signature_support: Mapping[frozenset[str], Counter[str]],
    ) -> frozenset[frozenset[str]]:
        """Return ambiguous goal signatures with enough cross-factory support.

        Extracted verbatim from the comprehension in ``ownership_context``.
        """

        return frozenset(
            signature
            for signature, per_factory in ambiguous_signature_support.items()
            if len(per_factory) >= 2
            and any(
                seen >= GOAL_FAMILY_MIN_SUPPORT
                for seen in per_factory.values()
            )
        )

    def ownership_context(self) -> dict[str, Any]:
        """Describe whether cross-factory ownership is safe for output.

        Curation may report an incomplete source, but it must not write a
        cleaned tree when any ownership axis is unresolved or when a signal
        names a home factory absent from the verified source context. Partial
        sources apply the stricter reviewed-signature boundary; a source that
        contains every reviewed factory may use the complete corpus as its
        reference index.
        """

        verified = {
            entry.factory for entry in self._entries if entry.factory_verified
        }
        reference_scope_complete, prefix_factories = self._reference_scope_state()

        identity = self._declared_identity()
        destinations = {entry.factory for entry in self._entries}
        unresolved_destinations = self._unresolved_destinations(
            destinations, identity
        )
        homes = self._prefix_homes(identity)
        goal_token_counts = self._goal_token_counts(homes, identity)
        vocabulary = self._goal_vocabulary(
            homes, identity, goal_token_counts=goal_token_counts
        )
        goal_homes = self._goal_family_homes(vocabulary, homes, identity)
        axes = _ResolvedAxes(identity=identity, homes=homes, vocabulary=vocabulary)
        raw_goal_candidates: dict[
            _Entry, tuple[str, frozenset[str]]
        ] = {}
        raw_goal_candidate_support: Counter[
            tuple[str, str, frozenset[str]]
        ] = Counter()
        for entry in self._entries:
            self._collect_raw_goal_candidate(
                entry, axes, raw_goal_candidates, raw_goal_candidate_support
            )
        unresolved_prefixes = self._unresolved_prefixes(prefix_factories, homes)
        missing_homes = self._missing_homes(homes, identity, verified)
        unresolved_goal_records: set[str] = set()
        reviewed_goal_tokens = frozenset(REVIEWED_GOAL_TOKEN_HOMES)
        ambiguous_goal_tokens = self._ambiguous_goal_tokens(
            goal_token_counts, reviewed_goal_tokens
        )
        ambiguous_accumulator = _AmbiguousSignatureAccumulator(
            signatures={}, support=defaultdict(Counter)
        )
        for entry in self._entries:
            self._collect_ambiguous_goal_signature(
                entry, axes, ambiguous_goal_tokens, ambiguous_accumulator
            )
        ambiguous_goal_signatures = ambiguous_accumulator.signatures
        ambiguous_signature_support = ambiguous_accumulator.support
        unresolved_ambiguous_signatures = self._unresolved_ambiguous_signatures(
            ambiguous_signature_support
        )
        context = _OwnershipResolutionContext(
            identity=identity,
            homes=homes,
            vocabulary=vocabulary,
            goal_homes=goal_homes,
            raw_goal_candidates=raw_goal_candidates,
            raw_goal_candidate_support=raw_goal_candidate_support,
            reference_scope_complete=reference_scope_complete,
            ambiguous_goal_signatures=ambiguous_goal_signatures,
            unresolved_ambiguous_signatures=unresolved_ambiguous_signatures,
            reviewed_goal_tokens=reviewed_goal_tokens,
            verified=verified,
        )
        for entry in self._entries:
            self._resolve_entry_goal_ownership(
                entry, context, unresolved_goal_records, missing_homes
            )
        missing_homes.discard(None)
        complete = (
            len(verified) >= 2
            and not unresolved_destinations
            and not unresolved_prefixes
            and not missing_homes
            and not unresolved_goal_records
        )
        return {
            "complete": complete,
            "reference_scope_complete": reference_scope_complete,
            "verified_factories": sorted(verified),
            "unresolved_destinations": unresolved_destinations,
            "unresolved_prefixes": unresolved_prefixes,
            "unresolved_goal_records": sorted(unresolved_goal_records),
            "missing_home_factories": sorted(missing_homes),
        }

    def _goal_token_counts(
        self,
        homes: Mapping[str, frozenset[str]],
        identity: Mapping[str, str | None],
    ) -> dict[str, Counter[str]]:
        """Count goal tokens using only records not known to be foreign."""

        counts: dict[str, Counter[str]] = defaultdict(Counter)
        for entry in self._entries:
            payload_foreign, prefix_foreign, factory = self._foreignness(
                entry, homes, identity
            )
            if prefix_foreign:
                # A record already known to come from elsewhere must not teach
                # this destination its vocabulary. An empty home set means the
                # prefix is unresolved, not foreign; it may still teach the
                # destination for report-only analysis while output remains
                # blocked by ``unresolved_prefixes``.
                continue
            if payload_foreign:
                continue
            for token in entry.goal_family:
                counts[token][factory] += 1
        return counts

    def _goal_vocabulary(
        self,
        homes: Mapping[str, frozenset[str]],
        identity: Mapping[str, str | None],
        *,
        goal_token_counts: Mapping[str, Counter[str]] | None = None,
    ) -> dict[str, frozenset[str]]:
        """Map each destination to goal tokens uniquely characteristic of it.

        Reviewed product terms are independent evidence. For other tokens,
        prefix- or payload-foreign records are excluded from the teaching set
        and ownership requires support in exactly one factory. A token observed
        in more than one factory remains ambiguous regardless of prevalence:
        contaminated records cannot win ownership merely by becoming denser.
        """

        counts = (
            self._goal_token_counts(homes, identity)
            if goal_token_counts is None
            else goal_token_counts
        )

        vocabulary: dict[str, set[str]] = defaultdict(set)
        for token, per_factory in counts.items():
            reviewed_home = REVIEWED_GOAL_TOKEN_HOMES.get(token)
            if reviewed_home is not None:
                vocabulary[reviewed_home].add(token)
                continue
            if len(per_factory) != 1:
                continue
            factory, seen = next(iter(per_factory.items()))
            if seen >= GOAL_FAMILY_MIN_SUPPORT:
                vocabulary[factory].add(token)
        return {
            factory: frozenset(tokens)
            for factory, tokens in vocabulary.items()
        }

    def _raw_goal_family_home(
        self,
        entry: _Entry,
        vocabulary: Mapping[str, frozenset[str]],
        factory: str | None = None,
        *,
        require_independent_anchor: bool = True,
    ) -> str | None:
        """Return the one other destination this goal clearly belongs to."""

        own_factory = factory or entry.factory
        own = vocabulary.get(own_factory, frozenset())
        if not entry.goal_family:
            return None
        own_score = len(entry.goal_family & own)
        scored = sorted(
            (
                (len(entry.goal_family & tokens), other_factory)
                for other_factory, tokens in vocabulary.items()
                if other_factory != own_factory
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
        best_tokens = entry.goal_family & vocabulary[best_factory]
        # Reviewed generic terms such as retry/backoff/jitter are useful only
        # when the same goal also carries a strong reviewed anchor for that
        # home. A goal may alternatively rely on corpus-derived unique tokens.
        # Without either form of independent evidence, repeated native records
        # can be falsely quarantined merely for using common operational words.
        has_strong_anchor = bool(
            best_tokens & REVIEWED_GOAL_STRONG_ANCHORS
        )
        has_corpus_derived_anchor = bool(
            best_tokens - frozenset(REVIEWED_GOAL_TOKEN_HOMES)
        )
        if (
            require_independent_anchor
            and not has_strong_anchor
            and not has_corpus_derived_anchor
        ):
            return None
        return best_factory

    def _goal_family_homes(
        self,
        vocabulary: Mapping[str, frozenset[str]],
        homes: Mapping[str, frozenset[str]],
        identity: Mapping[str, str | None],
    ) -> dict[_Entry, str]:
        """Return supported foreign goal homes without convicting one overlap.

        The same clean destination-to-home signal must recur on at least
        ``GOAL_FAMILY_MIN_SUPPORT`` records. Each candidate independently
        matches at least ``GOAL_FAMILY_MIN_FOREIGN_TOKENS`` terms; tokens are
        never pooled across partial matches. Prefix- or payload-foreign records
        already carry independent ownership evidence, so their goal-family
        detail is retained without this extra support threshold and they never
        contribute support for a goal-only finding against a native record.
        """

        candidates: dict[_Entry, str] = {}
        support: Counter[tuple[str, str]] = Counter()
        for entry in self._entries:
            payload_foreign, prefix_foreign, factory = self._foreignness(
                entry, homes, identity
            )
            goal_home = self._raw_goal_family_home(entry, vocabulary, factory)
            if goal_home is None:
                continue
            candidates[entry] = goal_home
            if not payload_foreign and not prefix_foreign:
                support[(factory, goal_home)] += 1

        supported: dict[_Entry, str] = {}
        for entry, goal_home in candidates.items():
            payload_foreign, prefix_foreign, factory = self._foreignness(
                entry, homes, identity
            )
            if (
                prefix_foreign
                or payload_foreign
                or support[(factory, goal_home)] >= GOAL_FAMILY_MIN_SUPPORT
            ):
                supported[entry] = goal_home
        return supported

    def findings(self) -> tuple[MillFinding, ...]:
        """Return every indexed record whose mill signals are foreign, in order."""

        identity = self._declared_identity()
        homes = self._prefix_homes(identity)
        vocabulary = self._goal_vocabulary(homes, identity)
        goal_homes = self._goal_family_homes(vocabulary, homes, identity)

        results: list[MillFinding] = []
        for entry in self._entries:
            reasons: list[str] = []
            expected = identity.get(entry.factory)
            payload_foreign, prefix_foreign, _ = self._foreignness(
                entry, homes, identity
            )
            if payload_foreign:
                reasons.append(REASON_FOREIGN_PAYLOAD_FACTORY)

            if prefix_foreign:
                reasons.append(REASON_FOREIGN_MILL_ID_PREFIX)

            goal_home = goal_homes.get(entry)
            if goal_home is not None:
                reasons.append(REASON_FOREIGN_MILL_GOAL_FAMILY)

            if not reasons:
                continue
            prefix_homes = homes.get(entry.mill_prefix, frozenset())
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
