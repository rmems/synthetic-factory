#!/usr/bin/env python3
"""Foreign-mill detection on the shapes that defeated the earlier detectors.

The census of record EXP-G46-LEFTOVER-MILL-CENSUS-001 found 40 published
records that were dest-stamped (``meta.factory`` equal to the directory they
sit in), carried no ``leftover`` token in their id, and used a generic episode
slug with no destination-family field. Neither a factory-mix check nor a
dest-field-absence check can see those. These tests pin the id-prefix and
goal-family axes that do.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from mill_family import (  # noqa: E402
    GOAL_FAMILY_MIN_FOREIGN_TOKENS,
    REASON_FOREIGN_MILL_GOAL_FAMILY,
    REASON_FOREIGN_MILL_ID_PREFIX,
    REASON_FOREIGN_PAYLOAD_FACTORY,
    REVIEWED_MILL_PREFIX_HOMES,
    MillIndex,
    declared_factory,
    goal_family,
    mill_prefix,
    record_id,
    summarize,
)

CACHE_STAMPEDE = "cache-stampede-factory"
GRAPHQL = "graphql-nplusone-factory"
DOCKER = "docker-build-cache-factory"
K8S = "k8s-crashloop-factory"
SEARCH = "search-index-rebuild-factory"


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


class MillSignals(unittest.TestCase):
    def test_mill_prefix_parsing(self):
        self.assertEqual(mill_prefix({"id": "gql-r1405-postgraphile-wrap"}), "gql")
        self.assertEqual(mill_prefix({"id": "cst-r01-ttl-expiry"}), "cst")
        self.assertEqual(mill_prefix({"id": "dbc-r1410-bk-cachemount-l3"}), "dbc")
        # Published rounds include an underscored round token.
        self.assertEqual(mill_prefix({"id": "cst-r4_29-sentry-projects-list"}), "cst")
        # A round suffix letter is part of the round, not the mill.
        self.assertEqual(mill_prefix({"id": "rlb-r135b-retry-after"}), "rlb")

    def test_ids_without_a_round_token_have_no_mill_prefix(self):
        for identifier in ("smoke-e1", "episode-17", "gql", "GQL-R1-X", ""):
            self.assertIsNone(mill_prefix({"id": identifier}), identifier)
        self.assertIsNone(mill_prefix({}))
        self.assertIsNone(mill_prefix("not a record"))

    def test_record_id_falls_back_to_meta(self):
        self.assertEqual(record_id({"meta": {"id": "gql-r1-x"}}), "gql-r1-x")
        self.assertEqual(record_id({"id": " gql-r1-x "}), "gql-r1-x")
        self.assertIsNone(record_id({"id": ""}))

    def test_declared_factory_reads_meta(self):
        self.assertEqual(declared_factory(DEST_STAMPED_MILL[0]), CACHE_STAMPEDE)
        self.assertIsNone(declared_factory({"meta": {}}))
        self.assertIsNone(declared_factory({"meta": "cache"}))

    def test_goal_family_drops_shared_leftover_vocabulary(self):
        family = goal_family(DEST_STAMPED_MILL[0])
        self.assertIn("postgraphile", family)
        self.assertIn("wrapmass", family)
        # Every lane in this corpus writes leftover/fix goals, so those words
        # cannot identify a mill.
        for neutral in ("leftover", "fix", "drop", "plant", "lattice", "after"):
            self.assertNotIn(neutral, family)

    def test_goal_family_covers_both_preference_sides(self):
        pair = {
            "chosen": {"goal": "resolve singleflight stampede"},
            "rejected": {"goal": "resolve dataloader batching"},
        }
        self.assertEqual(
            goal_family(pair), frozenset({"resolve", "singleflight", "stampede", "dataloader", "batching"})
        )


class DestStampedMill(unittest.TestCase):
    """The 40-record class: dest-stamped, no leftover-in-id, generic slug."""

    def setUp(self):
        self.findings = {
            finding.record_id: finding for finding in stampede_index().findings()
        }

    def test_dest_stamped_foreign_mill_is_detected(self):
        for record in DEST_STAMPED_MILL:
            finding = self.findings.get(record["id"])
            self.assertIsNotNone(finding, record["id"])
            self.assertEqual(finding.factory, CACHE_STAMPEDE)
            self.assertEqual(finding.mill_prefix, "gql")
            self.assertIn(REASON_FOREIGN_MILL_ID_PREFIX, finding.reason_codes)
            self.assertEqual(finding.home_factories, (GRAPHQL,))

    def test_destination_controls_and_home_records_are_clean(self):
        for record in STAMPEDE_CONTROLS + GRAPHQL_NATIVE:
            self.assertNotIn(record["id"], self.findings, record["id"])

    def test_factory_mix_alone_cannot_see_them(self):
        """meta.factory is the destination, so the payload-factory axis is silent."""
        for record in DEST_STAMPED_MILL:
            self.assertEqual(record["meta"]["factory"], CACHE_STAMPEDE)
            finding = self.findings[record["id"]]
            self.assertNotIn(REASON_FOREIGN_PAYLOAD_FACTORY, finding.reason_codes)

    def test_leftover_in_id_is_not_the_mill_test(self):
        """No flagged id says 'leftover'; a destination id that does is clean."""
        for record in DEST_STAMPED_MILL:
            self.assertNotIn("leftover", record["id"])
        self.assertIn("leftover", STAMPEDE_CONTROLS[2]["id"])
        self.assertNotIn(STAMPEDE_CONTROLS[2]["id"], self.findings)

    def test_foreign_native_prefix_is_detected_even_with_leftover_in_id(self):
        stray = episode(
            "sir-r1400-leftover3c-vespa-handoff",
            "Repair Vespa index rebuild handoff after schema generation rollover",
            CACHE_STAMPEDE,
        )
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray]),
            (SEARCH, SEARCH_NATIVE),
        )
        finding = next(
            item for item in mills.findings() if item.record_id == stray["id"]
        )
        self.assertIn("leftover", stray["id"])
        self.assertIn(REASON_FOREIGN_MILL_ID_PREFIX, finding.reason_codes)
        self.assertEqual(finding.home_factories, (SEARCH,))

    def test_no_destination_family_field_is_required(self):
        """Generic episode slugs: nothing but goal/steps, so absence proves nothing."""
        for record in DEST_STAMPED_MILL + STAMPEDE_CONTROLS:
            self.assertEqual(
                sorted(record),
                ["goal", "id", "meta", "outcome", "reward", "steps"],
            )

    def test_summarize_reports_the_destination_table(self):
        report = summarize(stampede_index().findings())
        self.assertEqual(report["records"], len(DEST_STAMPED_MILL))
        self.assertEqual(
            report["by_factory"],
            {CACHE_STAMPEDE: {"records": 2, "foreign_prefixes": {"gql": 2}}},
        )
        # Both surviving axes agree on these two: a graphql-mill id prefix and
        # a graphql-mill goal vocabulary inside a cache-stampede directory.
        self.assertEqual(
            report["reason_codes"],
            {REASON_FOREIGN_MILL_ID_PREFIX: 2, REASON_FOREIGN_MILL_GOAL_FAMILY: 2},
        )
        self.assertEqual(
            report["record_ids"], sorted(record["id"] for record in DEST_STAMPED_MILL)
        )
        self.assertFalse(report["record_ids_truncated"])

    def test_summarize_truncates_long_id_lists(self):
        report = summarize(stampede_index().findings(), id_limit=1)
        self.assertEqual(len(report["record_ids"]), 1)
        self.assertTrue(report["record_ids_truncated"])


class OwnershipResolution(unittest.TestCase):
    def test_a_prefix_used_only_in_one_factory_is_native(self):
        """An unreviewed alias used in one factory is native, not a mix."""
        mills = index_of(
            (
                "db-migration-repair-factory",
                [
                    episode("dbm-r01-backfill", "repair backfill ordering", "db-migration-repair-factory"),
                    episode("dbm-r02-preflight", "repair preflight ordering", "db-migration-repair-factory"),
                    episode("zzq-r03-rollback", "repair rollback ordering", "db-migration-repair-factory"),
                ],
            ),
        )
        identity = mills._declared_identity()
        self.assertEqual(
            mills._prefix_homes(identity)["zzq"],
            frozenset({"db-migration-repair-factory"}),
        )
        self.assertEqual(mills.findings(), ())

    def test_a_tied_prefix_is_never_called_foreign(self):
        mills = index_of(
            (CACHE_STAMPEDE, [episode("xyz-r01-a", "alpha beta gamma", CACHE_STAMPEDE)]),
            (GRAPHQL, [episode("xyz-r02-b", "alpha beta gamma", GRAPHQL)]),
        )
        self.assertEqual(
            [f.reason_codes for f in mills.findings() if REASON_FOREIGN_MILL_ID_PREFIX in f.reason_codes],
            [],
        )
        self.assertEqual(mills.ownership_context()["unresolved_prefixes"], ["xyz"])

    def test_unresolved_prefix_still_teaches_report_only_vocabulary(self):
        mills = index_of(
            (
                CACHE_STAMPEDE,
                [
                    episode(
                        f"xyz-r0{index}-cache",
                        "quuxalpha quuxbeta quuxgamma",
                        CACHE_STAMPEDE,
                    )
                    for index in (1, 2)
                ],
            ),
            (
                GRAPHQL,
                [
                    episode(
                        f"xyz-r1{index}-graphql",
                        "corgialpha corgibeta corgimedia",
                        GRAPHQL,
                    )
                    for index in (1, 2)
                ],
            ),
        )

        identity = mills._declared_identity()
        homes = mills._prefix_homes(identity)
        self.assertEqual(homes["xyz"], frozenset())
        vocabulary = mills._goal_vocabulary(homes, identity)
        self.assertIn("quuxalpha", vocabulary[CACHE_STAMPEDE])
        self.assertIn("corgialpha", vocabulary[GRAPHQL])
        self.assertFalse(mills.ownership_context()["complete"])

    def test_foreign_prefix_home_survives_a_larger_destination_batch(self):
        strays = [
            episode(
                f"gql-r150{index}-foreign-{index}",
                "Fix PostGraphile makeWrapResolvers wrapMass bind wrapPull unions",
                CACHE_STAMPEDE,
            )
            for index in range(3)
        ]
        mills = index_of(
            (CACHE_STAMPEDE, list(STAMPEDE_CONTROLS[:2]) + strays),
            (GRAPHQL, list(GRAPHQL_NATIVE[:2])),
        )
        findings = {item.record_id: item for item in mills.findings()}
        for stray in strays:
            finding = findings[stray["id"]]
            self.assertIn(REASON_FOREIGN_MILL_ID_PREFIX, finding.reason_codes)
            self.assertEqual(finding.home_factories, (GRAPHQL,))

    def test_reviewed_alias_cannot_be_reversed_by_a_pure_contaminated_destination(self):
        native_alias = episode(
            "dmr-r01-native-alias",
            "fix verify",
            "db-migration-repair-factory",
        )
        stray_aliases = [
            episode(
                f"dmr-r2{index}-stray-alias",
                "fix verify",
                CACHE_STAMPEDE,
            )
            for index in range(2)
        ]
        mills = index_of(
            (
                "db-migration-repair-factory",
                [native_alias]
                + [
                    episode(
                        f"dbm-r1{index}-native",
                        "fix verify",
                        "db-migration-repair-factory",
                    )
                    for index in range(9)
                ],
            ),
            (
                CACHE_STAMPEDE,
                stray_aliases,
            ),
        )

        prefix_findings = {
            item.record_id: item
            for item in mills.findings()
            if REASON_FOREIGN_MILL_ID_PREFIX in item.reason_codes
        }
        self.assertNotIn(native_alias["id"], prefix_findings)
        for stray_alias in stray_aliases:
            self.assertEqual(
                prefix_findings[stray_alias["id"]].home_factories,
                ("db-migration-repair-factory",),
            )
        self.assertEqual(mills.ownership_context()["unresolved_prefixes"], [])

    def test_unknown_alias_conflict_is_not_resolved_from_destination_purity(self):
        native_alias = episode(
            "xyz-r01-native-alias",
            "fix verify",
            "db-migration-repair-factory",
        )
        stray_aliases = [
            episode(
                f"xyz-r2{index}-stray-alias",
                "fix verify",
                CACHE_STAMPEDE,
            )
            for index in range(2)
        ]
        mills = index_of(
            (
                "db-migration-repair-factory",
                [
                    native_alias,
                    episode(
                        "dbm-r10-native",
                        "fix verify",
                        "db-migration-repair-factory",
                    ),
                ],
            ),
            (CACHE_STAMPEDE, stray_aliases),
        )

        prefix_findings = {
            item.record_id
            for item in mills.findings()
            if REASON_FOREIGN_MILL_ID_PREFIX in item.reason_codes
        }
        self.assertNotIn(native_alias["id"], prefix_findings)
        self.assertTrue(
            all(record["id"] not in prefix_findings for record in stray_aliases)
        )
        self.assertEqual(mills.ownership_context()["unresolved_prefixes"], ["xyz"])

    def test_unknown_alias_cannot_authorize_output_from_one_destination(self):
        mills = index_of(
            (
                CACHE_STAMPEDE,
                [episode("xyz-r20-unknown", "fix verify", CACHE_STAMPEDE)],
            ),
            (
                K8S,
                [episode("kcl-r01-native", "fix verify", K8S)],
            ),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(context["unresolved_prefixes"], ["xyz"])

    def test_empty_index_has_no_findings(self):
        self.assertEqual(MillIndex().findings(), ())
        self.assertEqual(summarize(())["records"], 0)

    def test_non_mapping_records_are_ignored(self):
        mills = MillIndex()
        mills.add(CACHE_STAMPEDE, ["not", "a", "record"], 0)
        mills.add(CACHE_STAMPEDE, None, 1)
        self.assertEqual(len(mills), 0)
        self.assertEqual(mills.findings(), ())


class PayloadFactoryAxis(unittest.TestCase):
    def test_a_foreign_declared_factory_is_flagged(self):
        stray = episode(
            "cst-r04-stray-declaration",
            "Resolve TTL expiry thundering herd with singleflight",
            DOCKER,
        )
        mills = index_of((CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray]))
        findings = {finding.record_id: finding for finding in mills.findings()}
        self.assertIn(stray["id"], findings)
        finding = findings[stray["id"]]
        self.assertIn(REASON_FOREIGN_PAYLOAD_FACTORY, finding.reason_codes)
        self.assertEqual(finding.declared_factory, DOCKER)
        self.assertEqual(finding.expected_factory, CACHE_STAMPEDE)

    def test_declared_identity_comes_from_payloads_not_directory_names(self):
        """A snapshot directory with an off-slug name must not flag everything."""
        mills = index_of(("staging-copy", STAMPEDE_CONTROLS))
        self.assertEqual(mills.findings(), ())

    def test_tied_snapshot_identity_keeps_ownership_context_incomplete(self):
        mills = index_of(
            (
                CACHE_STAMPEDE,
                [episode("cache-home", "fix verify", CACHE_STAMPEDE)],
            ),
            (
                GRAPHQL,
                [episode("graphql-home", "fix verify", GRAPHQL)],
            ),
            (
                "staging-copy",
                [
                    episode("snapshot-cache", "fix verify", CACHE_STAMPEDE),
                    episode("snapshot-graphql", "fix verify", GRAPHQL),
                ],
            ),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(
            context["unresolved_destinations"], ["staging-copy"]
        )

    def test_unverified_snapshot_identity_names_a_missing_home_factory(self):
        absent = "unknown-absent-factory"
        mills = index_of(
            (
                CACHE_STAMPEDE,
                [episode("cache-home", "fix verify", CACHE_STAMPEDE)],
            ),
            (
                GRAPHQL,
                [episode("graphql-home", "fix verify", GRAPHQL)],
            ),
            (
                "staging-copy",
                [episode("snapshot-unknown", "fix verify", absent)],
            ),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(context["unresolved_destinations"], [])
        self.assertEqual(context["missing_home_factories"], [absent])

    def test_verified_all_foreign_destination_keeps_its_directory_identity(self):
        stray = episode(
            "sir-r56-meili-swap",
            "fix verify",
            SEARCH,
        )
        mills = index_of(
            ("email-webhook-retry-factory", [stray]),
        )

        finding = mills.findings()[0]
        self.assertEqual(finding.record_id, stray["id"])
        self.assertIn(REASON_FOREIGN_PAYLOAD_FACTORY, finding.reason_codes)
        self.assertEqual(
            finding.expected_factory, "email-webhook-retry-factory"
        )
        self.assertEqual(
            mills.ownership_context()["missing_home_factories"], [SEARCH]
        )

    def test_native_prefix_is_not_reported_as_foreign_for_payload_only_mix(self):
        stray = episode(
            "cst-r04-stray-declaration",
            "Resolve TTL expiry thundering herd with singleflight",
            DOCKER,
        )
        report = summarize(
            index_of((CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray])).findings()
        )
        self.assertEqual(
            report["by_factory"][CACHE_STAMPEDE]["foreign_prefixes"], {}
        )


class GoalFamilyAxis(unittest.TestCase):
    def test_clean_two_factory_corpus_has_complete_ownership(self):
        context = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS[:2]),
            (GRAPHQL, GRAPHQL_NATIVE[:2]),
        ).ownership_context()

        self.assertTrue(context["complete"])
        self.assertFalse(context["reference_scope_complete"])
        self.assertEqual(context["unresolved_destinations"], [])
        self.assertEqual(context["unresolved_prefixes"], [])
        self.assertEqual(context["unresolved_goal_records"], [])
        self.assertEqual(context["missing_home_factories"], [])
        self.assertEqual(
            context["verified_factories"],
            sorted([CACHE_STAMPEDE, GRAPHQL]),
        )

    def test_full_reviewed_reference_scope_is_explicit(self):
        mills = MillIndex()
        for index, (prefix, factory) in enumerate(
            sorted(REVIEWED_MILL_PREFIX_HOMES.items()), 1
        ):
            mills.add(
                factory,
                episode(f"{prefix}-r{index:02d}-native", "fix verify", factory),
                (factory, prefix),
                factory_verified=True,
            )

        context = mills.ownership_context()
        self.assertTrue(context["reference_scope_complete"])
        self.assertTrue(context["complete"])
        self.assertEqual(context["unresolved_prefixes"], [])

    def test_factory_names_alone_do_not_complete_the_reference_scope(self):
        mills = MillIndex()
        covered_factories = set()
        for index, (prefix, factory) in enumerate(
            sorted(REVIEWED_MILL_PREFIX_HOMES.items()), 1
        ):
            if factory in covered_factories:
                continue
            covered_factories.add(factory)
            mills.add(
                factory,
                episode(f"{prefix}-r{index:02d}-native", "fix verify", factory),
                (factory, prefix),
                factory_verified=True,
            )

        context = mills.ownership_context()
        self.assertFalse(context["reference_scope_complete"])

    def test_full_reference_scope_keeps_shared_novel_goals_unresolved(self):
        mills = MillIndex()
        for index, (prefix, factory) in enumerate(
            sorted(REVIEWED_MILL_PREFIX_HOMES.items()), 1
        ):
            mills.add(
                factory,
                episode(f"{prefix}-r{index:02d}-native", "fix verify", factory),
                (factory, prefix),
                factory_verified=True,
            )

        shared_goal = "quuxwidget corgipath zibblecache"
        shared_records = [
            episode("gql-r91-shared-novel", shared_goal, GRAPHQL),
            episode("cst-r91-shared-novel", shared_goal, CACHE_STAMPEDE),
            episode("cst-r92-shared-novel", shared_goal, CACHE_STAMPEDE),
        ]
        for record in shared_records:
            factory = record["meta"]["factory"]
            mills.add(
                factory,
                record,
                (factory, record["id"]),
                factory_verified=True,
            )

        context = mills.ownership_context()
        self.assertTrue(context["reference_scope_complete"])
        self.assertFalse(context["complete"])
        self.assertEqual(
            context["unresolved_goal_records"],
            sorted(record["id"] for record in shared_records),
        )
        self.assertEqual(mills.findings(), ())

    def test_repeated_native_prefix_foreign_goal_family_is_flagged(self):
        # Same prefix and declared factory as their neighbours; only the
        # repeated goal vocabulary betrays which mill wrote them. One such
        # record is allowed to be a legitimate cross-domain task.
        strays = [
            episode(
                f"cst-r0{index}-postgraphile-wrap",
                "Fix PostGraphile makeWrapResolvers wrapMass bind wrapPull unions",
                CACHE_STAMPEDE,
            )
            for index in (5, 6)
        ]
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + strays),
            (GRAPHQL, GRAPHQL_NATIVE),
        )
        findings = {finding.record_id: finding for finding in mills.findings()}
        for stray in strays:
            finding = findings[stray["id"]]
            self.assertEqual(
                finding.reason_codes, (REASON_FOREIGN_MILL_GOAL_FAMILY,)
            )
            self.assertEqual(finding.goal_family_home, GRAPHQL)
            # The id prefix is native, so only the goal family fires.
            self.assertEqual(finding.mill_prefix, "cst")
            self.assertNotIn(REASON_FOREIGN_MILL_ID_PREFIX, finding.reason_codes)

    def test_single_native_cross_domain_tasks_are_not_goal_only_findings(self):
        native_cross_domain = [
            (
                "git-ops-recovery-factory",
                episode(
                    "gor-r864-rebase-reapply-cherry-picks-dup",
                    "Rebase the retry branch; keep jitter and remove duplicate backoff",
                    "git-ops-recovery-factory",
                ),
            ),
            (
                "incident-response-oncall-factory",
                episode(
                    "irc-r3807-stargz-timeout",
                    "Restore the stargz timeout after layers disappeared from the TOC",
                    "incident-response-oncall-factory",
                ),
            ),
            (
                "long-horizon-coding-factory",
                episode(
                    "lhc-r4680-coredns-cache-prefetch",
                    "Repair TTL expiry after a cache stampede hit CoreDNS",
                    "long-horizon-coding-factory",
                ),
            ),
        ]
        mills = index_of(
            *((factory, [record]) for factory, record in native_cross_domain),
            (
                "rate-limit-backoff-factory",
                [
                    episode(
                        f"rlb-r0{index}-native",
                        "Apply retry backoff jitter after throttling",
                        "rate-limit-backoff-factory",
                    )
                    for index in (1, 2)
                ],
            ),
            (
                DOCKER,
                [
                    episode(
                        f"dbc-r0{index}-native",
                        "Repair stargz layers and TOC metadata",
                        DOCKER,
                    )
                    for index in (1, 2)
                ],
            ),
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS),
        )

        finding_ids = {finding.record_id for finding in mills.findings()}
        for _factory, record in native_cross_domain:
            self.assertNotIn(record["id"], finding_ids)

    def test_repeated_generic_reviewed_terms_do_not_convict_native_records(self):
        native = [
            episode(
                f"ewr-r0{index}-delivery",
                "Retry webhook delivery with backoff and jitter",
                "email-webhook-retry-factory",
            )
            for index in (1, 2)
        ]
        mills = index_of(
            ("email-webhook-retry-factory", native),
            (
                "rate-limit-backoff-factory",
                [
                    episode(
                        f"rlb-r0{index}-native",
                        "Apply ratelimit throttling backoff jitter",
                        "rate-limit-backoff-factory",
                    )
                    for index in (1, 2)
                ],
            ),
        )

        findings = {item.record_id for item in mills.findings()}
        self.assertTrue(findings.isdisjoint(record["id"] for record in native))
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(
            context["unresolved_goal_records"],
            sorted(record["id"] for record in native),
        )

    def test_distinct_generic_signatures_do_not_pool_cohort_support(self):
        mills = MillIndex()
        for index, (prefix, factory) in enumerate(
            sorted(REVIEWED_MILL_PREFIX_HOMES.items()), 1
        ):
            mills.add(
                factory,
                episode(f"{prefix}-r{index:02d}-native", "fix verify", factory),
                (factory, prefix),
                factory_verified=True,
            )

        native = [
            episode(
                "ewr-r91-ttl-expiry-herd",
                "Repair TTL expiry herd in webhook delivery",
                "email-webhook-retry-factory",
            ),
            episode(
                "ewr-r92-stampede-thundering-refills",
                "Repair stampede thundering refills in webhook delivery",
                "email-webhook-retry-factory",
            ),
        ]
        for record in native:
            mills.add(
                "email-webhook-retry-factory",
                record,
                ("email-webhook-retry-factory", record["id"]),
                factory_verified=True,
            )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertTrue(context["reference_scope_complete"])
        self.assertTrue(context["complete"])
        self.assertEqual(context["unresolved_goal_records"], [])

    def test_strong_foreign_anchor_does_not_convict_singleton(self):
        singleton = episode(
            "irc-r3808-buildkit-solver-outage",
            "Restore the BuildKit cachemount exporter after a solver outage",
            "incident-response-oncall-factory",
        )
        mills = index_of(
            ("incident-response-oncall-factory", [singleton]),
            (
                DOCKER,
                [
                    episode(
                        f"dbc-r0{index}-native",
                        "Repair BuildKit cachemount exporter solver layers",
                        DOCKER,
                    )
                    for index in (1, 2)
                ],
            ),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(context["unresolved_goal_records"], [singleton["id"]])

    def test_unknown_goal_vocabulary_keeps_ownership_context_incomplete(self):
        stray = episode(
            "cst-r99-unregistered-family",
            "QuuxAlpha quuxBeta quuxGamma quuxDelta",
            CACHE_STAMPEDE,
        )
        k8s_controls = [
            episode(
                f"kcl-r0{index}-probe",
                "CrashLoopBackOff liveness probe container restart",
                K8S,
            )
            for index in (1, 2)
        ]
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray]),
            (K8S, k8s_controls),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(
            context["unresolved_goal_records"], [stray["id"]]
        )

    def test_native_reviewed_terms_do_not_hide_unknown_goal_vocabulary(self):
        stray = episode(
            "cst-r98-unknown-expiry-family",
            "TTL expiry QuuxAlpha quuxBeta quuxGamma",
            CACHE_STAMPEDE,
        )
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray]),
            (
                K8S,
                [
                    episode(
                        "kcl-r01-native",
                        "CrashLoopBackOff liveness probe container restart",
                        K8S,
                    )
                ],
            ),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(context["unresolved_goal_records"], [stray["id"]])

    def test_reviewed_goal_vocabulary_names_an_absent_home(self):
        stray = episode(
            "cst-r99-postgraphile-wrap",
            "PostGraphile makeWrapResolvers wrapMass bind wrapPull unions",
            CACHE_STAMPEDE,
        )
        k8s_controls = [
            episode(
                f"kcl-r0{index}-probe",
                "CrashLoopBackOff liveness probe container restart",
                K8S,
            )
            for index in (1, 2)
        ]
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray]),
            (K8S, k8s_controls),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(context["unresolved_goal_records"], [stray["id"]])
        self.assertEqual(context["missing_home_factories"], [GRAPHQL])

    def test_reviewed_docker_goal_vocabulary_names_an_absent_home(self):
        stray = episode(
            "cst-r99-buildkit-family",
            "BuildKit cachemount exporter solver layers",
            CACHE_STAMPEDE,
        )
        k8s_controls = [
            episode(
                f"kcl-r0{index}-probe",
                "CrashLoopBackOff liveness probe container restart",
                K8S,
            )
            for index in (1, 2)
        ]
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray]),
            (K8S, k8s_controls),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(context["unresolved_goal_records"], [stray["id"]])
        self.assertEqual(context["missing_home_factories"], [DOCKER])

    def test_a_thin_foreign_overlap_is_not_enough(self):
        stray = episode(
            "cst-r06-unrelated",
            "Fix wrapMass",
            CACHE_STAMPEDE,
        )
        self.assertLess(len(goal_family(stray)), GOAL_FAMILY_MIN_FOREIGN_TOKENS)
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray]),
            (GRAPHQL, GRAPHQL_NATIVE),
        )
        self.assertNotIn(
            stray["id"], {finding.record_id for finding in mills.findings()}
        )

    def test_repeated_strays_cannot_teach_reviewed_goal_vocabulary(self):
        strays = [
            episode(
                f"cst-r1{index}-postgraphile-wrap",
                "PostGraphile makeWrapResolvers wrapMass bind wrapPull unions",
                CACHE_STAMPEDE,
            )
            for index in range(2)
        ]
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + strays),
            (GRAPHQL, GRAPHQL_NATIVE),
        )
        findings = {item.record_id: item for item in mills.findings()}
        for stray in strays:
            self.assertEqual(
                findings[stray["id"]].reason_codes,
                (REASON_FOREIGN_MILL_GOAL_FAMILY,),
            )
            self.assertEqual(findings[stray["id"]].goal_family_home, GRAPHQL)

    def test_foreign_prefix_cannot_supply_goal_only_cohort_support(self):
        prefix_foreign = episode(
            "gql-r1405-analyzer-projection",
            "Repair analyzer globals projection",
            CACHE_STAMPEDE,
        )
        native_cross_domain = episode(
            "cst-r1406-analyzer-projection",
            "Repair analyzer globals projection",
            CACHE_STAMPEDE,
        )
        mills = index_of(
            (
                CACHE_STAMPEDE,
                STAMPEDE_CONTROLS + [prefix_foreign, native_cross_domain],
            ),
            (GRAPHQL, GRAPHQL_NATIVE),
        )

        findings = {item.record_id: item for item in mills.findings()}
        self.assertIn(prefix_foreign["id"], findings)
        self.assertNotIn(native_cross_domain["id"], findings)
        self.assertIn(
            REASON_FOREIGN_MILL_ID_PREFIX,
            findings[prefix_foreign["id"]].reason_codes,
        )
        context = mills.ownership_context()
        self.assertTrue(context["complete"])
        self.assertEqual(context["unresolved_goal_records"], [])

    def test_distinct_reviewed_families_form_one_foreign_home_cohort(self):
        strays = [
            episode(
                "cst-r900-postgraphile-variant",
                "PostGraphile makeWrapResolvers wrapMass",
                CACHE_STAMPEDE,
            ),
            episode(
                "cst-r901-hotchocolate-variant",
                "HotChocolate analyzer projection",
                CACHE_STAMPEDE,
            ),
        ]
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + strays),
            (GRAPHQL, GRAPHQL_NATIVE),
        )

        findings = {item.record_id: item for item in mills.findings()}
        for stray in strays:
            self.assertEqual(
                findings[stray["id"]].reason_codes,
                (REASON_FOREIGN_MILL_GOAL_FAMILY,),
            )
            self.assertEqual(findings[stray["id"]].goal_family_home, GRAPHQL)

    def test_partial_overlap_requires_independent_goal_anchor(self):
        strays = [
            episode(
                "cst-r910-analyzer-globals-projection",
                "Analyzer globals projection",
                CACHE_STAMPEDE,
            ),
            episode(
                "cst-r910b-analyzer-globals-projection",
                "Analyzer globals projection",
                CACHE_STAMPEDE,
            ),
            episode(
                "cst-r911-analyzer-globals-costold",
                "Analyzer globals costOld",
                CACHE_STAMPEDE,
            ),
            episode(
                "cst-r912-projection-postgraphile-wrapmass",
                "Projection PostGraphile wrapMass",
                CACHE_STAMPEDE,
            ),
        ]
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + strays),
            (GRAPHQL, GRAPHQL_NATIVE),
        )

        findings = {item.record_id: item for item in mills.findings()}
        self.assertNotIn(strays[0]["id"], findings)
        self.assertNotIn(strays[1]["id"], findings)
        self.assertEqual(
            set(findings), {record["id"] for record in strays[2:]}
        )
        for stray in strays[2:]:
            self.assertEqual(
                findings[stray["id"]].reason_codes,
                (REASON_FOREIGN_MILL_GOAL_FAMILY,),
            )
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(
            context["unresolved_goal_records"],
            sorted((strays[0]["id"], strays[1]["id"])),
        )

    def test_dense_goal_strays_cannot_win_vocabulary_ownership(self):
        strays = [
            episode(
                f"cst-r2{index}-postgraphile-wrap",
                "PostGraphile makeWrapResolvers wrapMass bind wrapPull unions",
                CACHE_STAMPEDE,
            )
            for index in range(3)
        ]
        graphql_records = list(GRAPHQL_NATIVE[:2]) + [
            episode(
                f"gql-r3{index}-neutral",
                "fix verify",
                GRAPHQL,
            )
            for index in range(8)
        ]
        mills = index_of(
            (CACHE_STAMPEDE, strays),
            (GRAPHQL, graphql_records),
        )

        findings = {item.record_id: item for item in mills.findings()}
        for record in strays:
            self.assertEqual(
                findings[record["id"]].reason_codes,
                (REASON_FOREIGN_MILL_GOAL_FAMILY,),
            )
            self.assertEqual(findings[record["id"]].goal_family_home, GRAPHQL)
        for record in GRAPHQL_NATIVE[:2]:
            self.assertNotIn(record["id"], findings)
        self.assertTrue(mills.ownership_context()["complete"])

    def test_unreviewed_shared_vocabulary_stays_ambiguous(self):
        shared_goal = "quuxalpha quuxbeta quuxgamma"
        mills = index_of(
            (
                CACHE_STAMPEDE,
                [
                    episode(f"cst-r4{index}-shared", shared_goal, CACHE_STAMPEDE)
                    for index in range(3)
                ],
            ),
            (
                GRAPHQL,
                [
                    episode(f"gql-r5{index}-shared", shared_goal, GRAPHQL)
                    for index in range(2)
                ],
            ),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(len(context["unresolved_goal_records"]), 5)

    def test_repeated_unknown_goals_cannot_self_authorize(self):
        strays = [
            episode(
                f"cst-r6{index}-unknown",
                "QuuxAlpha quuxBeta quuxGamma quuxDelta",
                CACHE_STAMPEDE,
            )
            for index in range(3)
        ]
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + strays),
            (
                K8S,
                [episode("kcl-r01-native", "fix verify", K8S)],
            ),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(
            context["unresolved_goal_records"],
            sorted(record["id"] for record in strays),
        )

    def test_repeated_foreign_goal_is_scored_without_native_vocabulary(self):
        strays = [
            episode(
                f"cache-copy-{index}",
                "PostGraphile makeWrapResolvers wrapMass bind wrapPull unions",
                CACHE_STAMPEDE,
            )
            for index in (1, 2)
        ]
        mills = index_of(
            (
                CACHE_STAMPEDE,
                [episode("cache-home", "fix verify", CACHE_STAMPEDE), *strays],
            ),
            (GRAPHQL, GRAPHQL_NATIVE[:2]),
        )

        findings = {item.record_id: item for item in mills.findings()}
        for stray in strays:
            self.assertEqual(
                findings[stray["id"]].reason_codes,
                (REASON_FOREIGN_MILL_GOAL_FAMILY,),
            )
            self.assertEqual(findings[stray["id"]].goal_family_home, GRAPHQL)
        self.assertTrue(mills.ownership_context()["complete"])

    def test_a_destination_without_vocabulary_is_not_judged(self):
        lone = episode("kcl-r01-crashloop", "resolve CrashLoopBackOff probe", K8S)
        mills = index_of(
            (K8S, [lone]),
            (GRAPHQL, GRAPHQL_NATIVE),
        )
        self.assertEqual(mills.findings(), ())


if __name__ == "__main__":
    unittest.main()
