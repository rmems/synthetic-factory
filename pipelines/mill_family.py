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
# Reviewed generator aliases are independent ownership evidence. The registry
# freezes every prefix observed in the read-only 2026-08-19 agentic census,
# including native aliases and the known cross-destination spills. Unknown
# aliases remain useful for report-only inference, but can never authorize a
# cleaned output until their ownership is reviewed and added here.
REVIEWED_MILL_PREFIX_HOMES = {
    "acm": "api-contract-migration-factory",
    "amc": "agent-memory-compaction-factory",
    "azr": "authz-regression-factory",
    "brw": "browser-tool-use-factory",
    "cei": "csv-excel-ingest-factory",
    "cer": "cascading-error-recovery-factory",
    "crp": "code-review-preference-factory",
    "cst": "cache-stampede-factory",
    "dbc": "docker-build-cache-factory",
    "dbm": "db-migration-repair-factory",
    "dlk": "distributed-lock-factory",
    "dmr": "db-migration-repair-factory",
    "dpr": "data-pipeline-repair-factory",
    "evh": "eval-harness-trajectory-factory",
    "ewr": "email-webhook-retry-factory",
    "ffd": "feature-flag-debug-factory",
    "flk": "flaky-test-quarantine-factory",
    "ftq": "flaky-test-quarantine-factory",
    "gor": "git-ops-recovery-factory",
    "gql": "graphql-nplusone-factory",
    "iac": "infra-as-code-factory",
    "irc": "incident-response-oncall-factory",
    "kcl": "k8s-crashloop-factory",
    "lef": "llm-eval-flakiness-factory",
    "lhc": "long-horizon-coding-factory",
    "lrd": "log-redaction-factory",
    "mac": "multi-agent-coordination-factory",
    "mdb": "monorepo-dep-bump-factory",
    "msd": "mcp-tool-schema-drift-factory",
    "ntp": "notebook-to-pipeline-factory",
    "obs": "observability-debug-factory",
    "pay": "payment-idempotency-factory",
    "pbc": "proto-breaking-change-factory",
    "pci": "prompt-cache-invalidation-factory",
    "pid": "payment-idempotency-factory",
    "pkg": "package-release-factory",
    "qbp": "queue-backpressure-factory",
    "rag": "rag-retrieval-debug-factory",
    "rlb": "rate-limit-backoff-factory",
    "saf": "safety-calibration-factory",
    "sbox": "sandbox-refusal-factory",
    "scr": "ssl-cert-rotation-factory",
    "sir": "search-index-rebuild-factory",
    "srl": "sparse-reward-long-task-factory",
    "ssl": "ssl-cert-rotation-factory",
    "ssr": "secret-scan-remediation-factory",
    "tup": "tool-use-preference-factory",
    "wsr": "websocket-reconnect-factory",
}

# Distinctive vocabulary from the source and destination mills in the frozen
# #44 census. Generic words stay corpus-derived; only generator/product terms
# whose ownership was independently reviewed are pinned here. These signatures
# are also the closed-world boundary for authorizing cleaned output: novel goal
# families in one of these lanes stay unresolved instead of teaching
# themselves through repetition.
REVIEWED_GOAL_TOKEN_HOMES = {
    "crashloopbackoff": "k8s-crashloop-factory",
    "expiry": "cache-stampede-factory",
    "herd": "cache-stampede-factory",
    "liveness": "k8s-crashloop-factory",
    "probe": "k8s-crashloop-factory",
    "refills": "cache-stampede-factory",
    "restart": "k8s-crashloop-factory",
    "singleflight": "cache-stampede-factory",
    "stampede": "cache-stampede-factory",
    "throttling": "rate-limit-backoff-factory",
    "thundering": "cache-stampede-factory",
    "ttl": "cache-stampede-factory",
    "backoff": "rate-limit-backoff-factory",
    "jitter": "rate-limit-backoff-factory",
    "ratelimit": "rate-limit-backoff-factory",
    "retry": "rate-limit-backoff-factory",
    "buildkit": "docker-build-cache-factory",
    "blobcache": "docker-build-cache-factory",
    "cachemount": "docker-build-cache-factory",
    "estargz": "docker-build-cache-factory",
    "exporter": "docker-build-cache-factory",
    "layers": "docker-build-cache-factory",
    "nydus": "docker-build-cache-factory",
    "overlayfs": "docker-build-cache-factory",
    "rafs": "docker-build-cache-factory",
    "solver": "docker-build-cache-factory",
    "stargz": "docker-build-cache-factory",
    "toc": "docker-build-cache-factory",
    "whiteout": "docker-build-cache-factory",
    "analyzer": "graphql-nplusone-factory",
    "costnew": "graphql-nplusone-factory",
    "costold": "graphql-nplusone-factory",
    "edgedb": "graphql-nplusone-factory",
    "globalberth": "graphql-nplusone-factory",
    "globals": "graphql-nplusone-factory",
    "globalyard": "graphql-nplusone-factory",
    "hotchocolate": "graphql-nplusone-factory",
    "makewrapresolvers": "graphql-nplusone-factory",
    "postgraphile": "graphql-nplusone-factory",
    "projection": "graphql-nplusone-factory",
    "wrapmass": "graphql-nplusone-factory",
    "wrappull": "graphql-nplusone-factory",
}

# One record can legitimately cross domain boundaries: a Git recovery task can
# mention retry jitter, an on-call incident can involve stargz, and a coding
# task can repair a cache stampede. These strong anchors distinguish a reviewed
# product signature from generic reviewed words. They never convict a different
# home by themselves: goal-only foreign evidence must still recur as an
# independently clean cohort.
REVIEWED_GOAL_STRONG_ANCHORS = frozenset(
    {
        "singleflight",
        "crashloopbackoff",
        "ratelimit",
        "blobcache",
        "buildkit",
        "cachemount",
        "estargz",
        "nydus",
        "overlayfs",
        "rafs",
        "costnew",
        "costold",
        "edgedb",
        "globalberth",
        "globalyard",
        "hotchocolate",
        "makewrapresolvers",
        "postgraphile",
        "wrapmass",
        "wrappull",
    }
)


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
    """Return the unambiguous factory the payload claims for itself.

    Preference wrappers often carry provenance on `chosen` and `rejected`
    instead of at the root. Two agreeing side stamps identify the origin even
    when the publication-required wrapper stamp names the destination; side
    disagreement is ambiguous and deliberately resolves to nothing.
    """

    if not isinstance(record, Mapping):
        return None

    def stamp(container: Any) -> str | None:
        if not isinstance(container, Mapping):
            return None
        meta = container.get("meta")
        if not isinstance(meta, Mapping):
            return None
        value = meta.get("factory")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    root = stamp(record)
    stamped_sides = [
        value
        for side in ("chosen", "rejected")
        if (value := stamp(record.get(side))) is not None
    ]
    side_stamps = set(stamped_sides)
    if len(side_stamps) > 1:
        return None
    if len(stamped_sides) == 2:
        # Agentic publication stamps the wrapper with its destination. Two
        # agreeing side stamps are therefore stronger evidence of the pair's
        # originating factory, including when it differs from that wrapper.
        return stamped_sides[0]
    if root is not None:
        return root
    return next(iter(side_stamps)) if side_stamps else None


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
            if entry.mill_prefix is not None:
                factory = (
                    identity.get(entry.factory) if identity is not None else None
                ) or entry.factory
                counts[entry.mill_prefix][factory] += 1
                if entry.declared_factory is not None:
                    declarations[entry.mill_prefix].add(entry.declared_factory)
        homes: dict[str, frozenset[str]] = {}
        for prefix, per_factory in counts.items():
            reviewed_home = REVIEWED_MILL_PREFIX_HOMES.get(prefix)
            if reviewed_home is not None:
                homes[prefix] = frozenset({reviewed_home})
                continue
            declared = declarations[prefix]
            if len(declared) == 1:
                homes[prefix] = frozenset(declared)
                continue
            if len(per_factory) == 1:
                homes[prefix] = frozenset(per_factory)
                continue
            homes[prefix] = frozenset()
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
        cleaned tree when any ownership axis is unresolved or when a signal
        names a home factory absent from the verified source context. Partial
        sources apply the stricter reviewed-signature boundary; a source that
        contains every reviewed factory may use the complete corpus as its
        reference index.
        """

        verified = {
            entry.factory for entry in self._entries if entry.factory_verified
        }
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

        identity = self._declared_identity()
        destinations = {entry.factory for entry in self._entries}
        unresolved_destinations = sorted(
            factory
            for factory in destinations
            if identity.get(factory) is None
        )
        homes = self._prefix_homes(identity)
        goal_token_counts = self._goal_token_counts(homes, identity)
        vocabulary = self._goal_vocabulary(
            homes, identity, goal_token_counts=goal_token_counts
        )
        goal_homes = self._goal_family_homes(vocabulary, homes, identity)
        raw_goal_candidates: dict[
            _Entry, tuple[str, frozenset[str]]
        ] = {}
        raw_goal_candidate_support: Counter[
            tuple[str, str, frozenset[str]]
        ] = Counter()
        for entry in self._entries:
            factory = identity.get(entry.factory) or entry.factory
            candidate = self._raw_goal_family_home(
                entry,
                vocabulary,
                factory,
                require_independent_anchor=False,
            )
            if candidate is None:
                continue
            candidate_signature = frozenset(
                entry.goal_family & vocabulary[candidate]
            )
            raw_goal_candidates[entry] = (candidate, candidate_signature)
            prefix_homes = homes.get(entry.mill_prefix, frozenset())
            payload_foreign = (
                entry.declared_factory is not None
                and identity.get(entry.factory) is not None
                and entry.declared_factory != identity.get(entry.factory)
            )
            prefix_foreign = (
                entry.mill_prefix is not None
                and prefix_homes
                and factory not in prefix_homes
            )
            if not payload_foreign and not prefix_foreign:
                raw_goal_candidate_support[
                    (factory, candidate, candidate_signature)
                ] += 1
        unresolved_prefixes = sorted(
            prefix
            for prefix, factories in prefix_factories.items()
            if prefix not in REVIEWED_MILL_PREFIX_HOMES
            or (len(factories) > 1 and not homes.get(prefix))
        )
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
        unresolved_goal_records: set[str] = set()
        reviewed_goal_tokens = frozenset(REVIEWED_GOAL_TOKEN_HOMES)
        ambiguous_goal_tokens = frozenset(
            token
            for token, per_factory in goal_token_counts.items()
            if token not in reviewed_goal_tokens
            and len(per_factory) >= 2
            and any(
                seen >= GOAL_FAMILY_MIN_SUPPORT
                for seen in per_factory.values()
            )
        )
        ambiguous_goal_signatures: dict[
            _Entry, frozenset[str]
        ] = {}
        ambiguous_signature_support: dict[
            frozenset[str], Counter[str]
        ] = defaultdict(Counter)
        for entry in self._entries:
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
            signature = frozenset(
                entry.goal_family & ambiguous_goal_tokens
            )
            if (
                payload_foreign
                or prefix_foreign
                or len(signature) < GOAL_FAMILY_MIN_FOREIGN_TOKENS
            ):
                continue
            ambiguous_goal_signatures[entry] = signature
            ambiguous_signature_support[signature][effective_factory] += 1
        unresolved_ambiguous_signatures = frozenset(
            signature
            for signature, per_factory in ambiguous_signature_support.items()
            if len(per_factory) >= 2
            and any(
                seen >= GOAL_FAMILY_MIN_SUPPORT
                for seen in per_factory.values()
            )
        )
        for entry in self._entries:
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
            if payload_foreign or prefix_foreign:
                continue

            goal_home = goal_homes.get(entry)
            if goal_home is not None:
                if goal_home not in verified:
                    missing_homes.add(goal_home)
                continue

            raw_goal_candidate = raw_goal_candidates.get(entry)
            independently_anchored_candidate = self._raw_goal_family_home(
                entry, vocabulary, effective_factory
            )
            if (
                raw_goal_candidate is not None
                and independently_anchored_candidate is None
                and raw_goal_candidate_support[
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
                unresolved_goal_records.add(
                    entry.record_id
                    or (
                        str(entry.ref)
                        if entry.ref is not None
                        else "<unknown>"
                    )
                )
                if raw_goal_candidate[0] not in verified:
                    missing_homes.add(raw_goal_candidate[0])
                continue

            if reference_scope_complete:
                # Full reviewed-prefix coverage does not resolve a novel goal
                # family repeated in multiple factories. Those tokens were
                # deliberately omitted from ``vocabulary`` as ambiguous; keep
                # their records unresolved instead of treating the omission as
                # permission to export them.
                if (
                    ambiguous_goal_signatures.get(entry)
                    in unresolved_ambiguous_signatures
                ):
                    unresolved_goal_records.add(
                        entry.record_id
                        or (
                            str(entry.ref)
                            if entry.ref is not None
                            else "<unknown>"
                        )
                    )
                continue

            # A singleton can resemble a reviewed foreign family while still
            # being a legitimate cross-domain task. Do not quarantine it on
            # that resemblance alone, but do fail a partial export closed: the
            # complete audited reference scope is what establishes that the
            # singleton is not part of a repeated foreign cohort.
            raw_goal_home = self._raw_goal_family_home(
                entry, vocabulary, effective_factory
            )
            if raw_goal_home is not None:
                unresolved_goal_records.add(
                    entry.record_id
                    or (str(entry.ref) if entry.ref is not None else "<unknown>")
                )
                if raw_goal_home not in verified:
                    missing_homes.add(raw_goal_home)
                continue

            has_native_strong_anchor = any(
                token in REVIEWED_GOAL_STRONG_ANCHORS
                and REVIEWED_GOAL_TOKEN_HOMES.get(token) == effective_factory
                for token in entry.goal_family
            )
            unknown_score = len(entry.goal_family - reviewed_goal_tokens)
            if (
                unknown_score >= GOAL_FAMILY_MIN_FOREIGN_TOKENS
                and not has_native_strong_anchor
            ):
                unresolved_goal_records.add(
                    entry.record_id
                    or (str(entry.ref) if entry.ref is not None else "<unknown>")
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
            prefix = entry.mill_prefix
            expected = identity.get(entry.factory)
            factory = expected or entry.factory
            prefix_homes = (
                homes.get(prefix, frozenset())
                if prefix is not None
                else frozenset()
            )
            if prefix_homes and factory not in prefix_homes:
                # A record already known to come from elsewhere must not teach
                # this destination its vocabulary. An empty home set means the
                # prefix is unresolved, not foreign; it may still teach the
                # destination for report-only analysis while output remains
                # blocked by ``unresolved_prefixes``.
                continue
            if (
                entry.declared_factory is not None
                and expected is not None
                and entry.declared_factory != expected
            ):
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
            factory = identity.get(entry.factory) or entry.factory
            goal_home = self._raw_goal_family_home(entry, vocabulary, factory)
            if goal_home is None:
                continue
            candidates[entry] = goal_home
            prefix_homes = homes.get(entry.mill_prefix, frozenset())
            payload_foreign = (
                entry.declared_factory is not None
                and identity.get(entry.factory) is not None
                and entry.declared_factory != identity.get(entry.factory)
            )
            prefix_foreign = (
                entry.mill_prefix is not None
                and prefix_homes
                and factory not in prefix_homes
            )
            if not payload_foreign and not prefix_foreign:
                support[(factory, goal_home)] += 1

        supported: dict[_Entry, str] = {}
        for entry, goal_home in candidates.items():
            factory = identity.get(entry.factory) or entry.factory
            prefix_homes = homes.get(entry.mill_prefix, frozenset())
            prefix_foreign = (
                entry.mill_prefix is not None
                and prefix_homes
                and factory not in prefix_homes
            )
            expected = identity.get(entry.factory)
            payload_foreign = (
                entry.declared_factory is not None
                and expected is not None
                and entry.declared_factory != expected
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

            goal_home = goal_homes.get(entry)
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
