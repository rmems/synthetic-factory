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
        """An alias prefix (dmr- beside dbm-) is that factory's own, not a mix."""
        mills = index_of(
            (
                "db-migration-repair-factory",
                [
                    episode("dbm-r01-backfill", "repair backfill ordering", "db-migration-repair-factory"),
                    episode("dbm-r02-preflight", "repair preflight ordering", "db-migration-repair-factory"),
                    episode("dmr-r03-rollback", "repair rollback ordering", "db-migration-repair-factory"),
                ],
            ),
        )
        self.assertEqual(mills.findings(), ())

    def test_a_tied_prefix_is_never_called_foreign(self):
        mills = index_of(
            (CACHE_STAMPEDE, [episode("gql-r01-a", "alpha beta gamma", CACHE_STAMPEDE)]),
            (GRAPHQL, [episode("gql-r02-b", "alpha beta gamma", GRAPHQL)]),
        )
        self.assertEqual(
            [f.reason_codes for f in mills.findings() if REASON_FOREIGN_MILL_ID_PREFIX in f.reason_codes],
            [],
        )

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

    def test_maximum_prefix_share_cannot_reverse_a_rare_native_alias(self):
        native_alias = episode(
            "dmr-r01-native-alias",
            "fix verify",
            "db-migration-repair-factory",
        )
        stray_alias = episode(
            "dmr-r20-stray-alias",
            "fix verify",
            CACHE_STAMPEDE,
        )
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
                [stray_alias]
                + [
                    episode(
                        f"cst-r2{index}-native",
                        "fix verify",
                        CACHE_STAMPEDE,
                    )
                    for index in range(4)
                ],
            ),
        )

        prefix_findings = {
            item.record_id
            for item in mills.findings()
            if REASON_FOREIGN_MILL_ID_PREFIX in item.reason_codes
        }
        self.assertNotIn(native_alias["id"], prefix_findings)
        self.assertNotIn(stray_alias["id"], prefix_findings)
        self.assertEqual(
            mills.ownership_context()["unresolved_prefixes"], ["dmr"]
        )

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
    def test_native_prefix_with_a_foreign_goal_family_is_flagged(self):
        # Same prefix and declared factory as its neighbours; only the goal
        # vocabulary betrays which mill wrote it.
        stray = episode(
            "cst-r05-postgraphile-wrap",
            "Fix PostGraphile makeWrapResolvers wrapMass bind wrapPull unions",
            CACHE_STAMPEDE,
        )
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray]),
            (GRAPHQL, GRAPHQL_NATIVE),
        )
        findings = {finding.record_id: finding for finding in mills.findings()}
        self.assertIn(stray["id"], findings)
        finding = findings[stray["id"]]
        self.assertEqual(finding.reason_codes, (REASON_FOREIGN_MILL_GOAL_FAMILY,))
        self.assertEqual(finding.goal_family_home, GRAPHQL)
        # The id prefix is the destination's own, so only the goal family fires.
        self.assertEqual(finding.mill_prefix, "cst")
        self.assertNotIn(REASON_FOREIGN_MILL_ID_PREFIX, finding.reason_codes)

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

    def test_repeated_strays_do_not_teach_the_destination_vocabulary(self):
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
            self.assertEqual(
                findings[stray["id"]].goal_family_home,
                GRAPHQL,
            )

    def test_a_destination_without_vocabulary_is_not_judged(self):
        lone = episode("kcl-r01-crashloop", "resolve CrashLoopBackOff probe", K8S)
        mills = index_of(
            (K8S, [lone]),
            (GRAPHQL, GRAPHQL_NATIVE),
        )
        self.assertEqual(mills.findings(), ())


if __name__ == "__main__":
    unittest.main()
