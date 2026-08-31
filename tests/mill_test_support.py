#!/usr/bin/env python3
"""Shared fixtures for the foreign-mill detection suites.

Every mill suite judges the same corpus shape: a destination factory directory
holding its own records plus a few strays, against the home factories that
establish what those strays' id prefix and goal vocabulary really belong to.
This module builds those corpora, the ``MillIndex`` around them, and the
verdict assertions the axis suites share, so each suite writes only the records
its own axis is about.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from mill_family import (  # noqa: E402
    REASON_FOREIGN_MILL_GOAL_FAMILY,
    REASON_FOREIGN_PAYLOAD_FACTORY,
    REVIEWED_MILL_PREFIX_HOMES,
    MillIndex,
)

CACHE_STAMPEDE = "cache-stampede-factory"
GRAPHQL = "graphql-nplusone-factory"
DOCKER = "docker-build-cache-factory"
K8S = "k8s-crashloop-factory"
SEARCH = "search-index-rebuild-factory"
AGENTIC_CODING = "agentic-coding-trajectory-factory"
DB_MIGRATION = "db-migration-repair-factory"
EMAIL_WEBHOOK = "email-webhook-retry-factory"
RATE_LIMIT = "rate-limit-backoff-factory"
INCIDENT_RESPONSE = "incident-response-oncall-factory"

# Goals the suites reuse verbatim. NEUTRAL_GOAL carries stopwords only, so it
# teaches no destination any vocabulary; the others are the reviewed graphql
# and k8s families, and a family no reviewed factory owns.
NEUTRAL_GOAL = "fix verify"
GRAPHQL_WRAP_GOAL = "PostGraphile makeWrapResolvers wrapMass bind wrapPull unions"
K8S_PROBE_GOAL = "CrashLoopBackOff liveness probe container restart"
UNKNOWN_GOAL = "QuuxAlpha quuxBeta quuxGamma quuxDelta"


def episode(record_id_value, goal, factory, **overrides):
    """A generic episode slug: goal + steps, no destination-family field."""
    record = {
        "id": record_id_value,
        "goal": goal,
        "steps": [
            {
                "n": 1,
                "decision_basis": "Observation: the probe reproduced the report",
                "tool_call": {"name": "bash", "args": {"command": "run"}},
                "observation": "reproduced",
            }
        ],
        "outcome": "resolved",
        "reward": {"success": True},
        "meta": {"factory": factory, "round": 1, "generator": "grok-4.6"},
    }
    record.update(overrides)
    return record


# Destination controls: real cache-stampede goals, cst- prefix, dest-stamped.
STAMPEDE_CONTROLS = [
    episode(
        "cst-r01-ttl-expiry-thundering-herd",
        "Resolve TTL expiry thundering herd on the pricing cache: "
        "add singleflight so one origin request refills the cache.",
        CACHE_STAMPEDE,
    ),
    episode(
        "cst-r02-singleflight-lock-timeout",
        "Resolve stampede on the session cache: the singleflight lock times "
        "out and every request refills the origin.",
        CACHE_STAMPEDE,
    ),
    episode(
        "cst-r03-leftover-cache-key-herd",
        "Resolve leftover cache key thundering herd: singleflight refills the "
        "origin under the wrong cache key.",
        CACHE_STAMPEDE,
    ),
]

# The mill's own records, in its own directory. Establishes gql- ownership.
GRAPHQL_NATIVE = [
    episode(
        "gql-r1400-postgraphile-wrap-resolver",
        "Fix PostGraphile makeWrapResolvers leftover after plugin order swap: "
        "leftover wrapMass after bind to wrapPull. Do not drop wrap resolvers.",
        GRAPHQL,
    ),
    episode(
        "gql-r1401-postgraphile-plugin-order",
        "Fix PostGraphile makeWrapResolvers leftover after plugin order swap "
        "on unions: leftover wrapMass after bind to wrapPull.",
        GRAPHQL,
    ),
    episode(
        "gql-r1402-hotchocolate-projection",
        "Fix HotChocolate cost-analyzer leftover after projection rewrite: "
        "leftover costOld after bind to costNew. Do not disable cost analyzer.",
        GRAPHQL,
    ),
    episode(
        "gql-r1403-edgedb-globals",
        "Fix EdgeDB GraphQL globals leftover after access-policy rewrite: "
        "leftover globalYard after bind to globalBerth.",
        GRAPHQL,
    ),
]

SEARCH_NATIVE = [
    episode(
        "sir-r1300-vespa-index-handoff",
        "Repair Vespa index rebuild handoff after schema generation rollover",
        SEARCH,
    ),
    episode(
        "sir-r1301-elasticsearch-alias-swap",
        "Repair Elasticsearch index rebuild alias swap after shard recovery",
        SEARCH,
    ),
]

# The #44 class: graphql-mill records published into cache-stampede, stamped
# with the destination factory, with no 'leftover' token in the id.
DEST_STAMPED_MILL = [
    episode(
        "gql-r1405-postgraphile-wrap-resolver-after-plugin-order",
        "Fix PostGraphile makeWrapResolvers leftover after plugin order swap "
        "on plant lattice-hawsepike: leftover wrapMass after bind to wrapPull. "
        "Do not drop wrap resolvers.",
        CACHE_STAMPEDE,
    ),
    episode(
        "gql-r1405-postgraphile-drop-wrap",
        "Partial-fix PostGraphile makeWrapResolvers leftover after plugin "
        "order swap fail path on lattice-hawsepike: leftover wrapMass on "
        "unions after wrapPull. Do not drop wrap resolvers.",
        CACHE_STAMPEDE,
    ),
]


def index_of(*groups):
    mills = MillIndex()
    for factory, records in groups:
        for offset, record in enumerate(records):
            mills.add(
                factory,
                record,
                (factory, record["id"], offset),
                factory_verified=factory.endswith("-factory"),
            )
    return mills


def stampede_index():
    return index_of(
        (CACHE_STAMPEDE, STAMPEDE_CONTROLS + DEST_STAMPED_MILL),
        (GRAPHQL, GRAPHQL_NATIVE),
    )


def finding_map(mills):
    """Every finding the index reports, keyed by the record it convicts."""
    return {finding.record_id: finding for finding in mills.findings()}


def stampede_only_index(stray):
    """One stray in the cache-stampede directory, with no other destination."""
    return index_of((CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray]))


def strays_against_graphql(strays, natives=GRAPHQL_NATIVE):
    """Strays in the cache-stampede directory, judged against the graphql mill."""
    return index_of(
        (CACHE_STAMPEDE, STAMPEDE_CONTROLS + list(strays)),
        (GRAPHQL, natives),
    )


def k8s_probe_controls(count=2):
    """Native k8s records carrying that destination's own goal vocabulary."""
    return [
        episode(f"kcl-r0{index}-probe", K8S_PROBE_GOAL, K8S)
        for index in range(1, count + 1)
    ]


def stray_against_k8s(stray, controls=2):
    """One stray in cache-stampede, with a vocabulary-bearing k8s as the only
    other home: nothing there can own a graphql or buildkit goal family."""
    return index_of(
        (CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray]),
        (K8S, k8s_probe_controls(controls)),
    )


def alias_conflict_index(prefix, native_fillers):
    """One alias prefix claimed by a home factory and by a destination.

    ``prefix`` appears once natively in ``db-migration-repair-factory`` and
    twice as a stray in the cache-stampede directory; ``native_fillers`` is how
    many unambiguous ``dbm-`` records back the home directory up. Returns the
    index, the native alias record, and the stray alias records.
    """
    native_alias = episode(f"{prefix}-r01-native-alias", NEUTRAL_GOAL, DB_MIGRATION)
    stray_aliases = [
        episode(f"{prefix}-r2{index}-stray-alias", NEUTRAL_GOAL, CACHE_STAMPEDE)
        for index in range(2)
    ]
    natives = [native_alias] + [
        episode(f"dbm-r1{index}-native", NEUTRAL_GOAL, DB_MIGRATION)
        for index in range(native_fillers)
    ]
    mills = index_of((DB_MIGRATION, natives), (CACHE_STAMPEDE, stray_aliases))
    return mills, native_alias, stray_aliases


def _reviewed_natives():
    """One native record per reviewed prefix, in a stable order."""
    for index, (prefix, factory) in enumerate(
        sorted(REVIEWED_MILL_PREFIX_HOMES.items()), 1
    ):
        record = episode(f"{prefix}-r{index:02d}-native", NEUTRAL_GOAL, factory)
        yield factory, prefix, record


def reviewed_reference_index():
    """A verified index holding one native record for every reviewed prefix."""
    mills = MillIndex()
    for factory, prefix, record in _reviewed_natives():
        mills.add(factory, record, (factory, prefix), factory_verified=True)
    return mills


def reviewed_factory_index():
    """One native record per reviewed *factory*: every reviewed home is present
    but most reviewed prefixes are not."""
    mills = MillIndex()
    covered_factories = set()
    for factory, prefix, record in _reviewed_natives():
        if factory in covered_factories:
            continue
        covered_factories.add(factory)
        mills.add(factory, record, (factory, prefix), factory_verified=True)
    return mills


def add_verified(mills, records):
    """Index already-stamped records into the destination they declare."""
    for record in records:
        factory = record["meta"]["factory"]
        mills.add(factory, record, (factory, record["id"]), factory_verified=True)


class MillAxisAssertions:
    """Verdict assertions shared by the mill axis suites."""

    def assert_goal_family_home(self, mills, records, home):
        """Every record is convicted on the goal axis alone, and owned by ``home``."""
        findings = finding_map(mills)
        for record in records:
            finding = findings[record["id"]]
            self.assertEqual(finding.reason_codes, (REASON_FOREIGN_MILL_GOAL_FAMILY,))
            self.assertEqual(finding.goal_family_home, home)
        return findings

    def assert_unresolved_goal_records(self, mills, records):
        """Nothing is convicted, and the run still cannot be called owned."""
        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(
            context["unresolved_goal_records"],
            sorted(record["id"] for record in records),
        )
        return context

    def assert_declared_factory_finding(self, mills, stray, declared):
        """The payload axis names ``declared`` as the record's own factory."""
        findings = finding_map(mills)
        self.assertIn(stray["id"], findings)
        finding = findings[stray["id"]]
        self.assertIn(REASON_FOREIGN_PAYLOAD_FACTORY, finding.reason_codes)
        self.assertEqual(finding.declared_factory, declared)
        return finding
