#!/usr/bin/env python3
"""Where each mill id prefix lives, resolved across a whole run.

The prefix axis only convicts once the run says which factory a prefix belongs
to. These tests pin how that home is established and, more importantly, when it
must refuse to be established: a prefix used in one place only, a prefix two
destinations tie over, an alias a contaminated destination would otherwise
reverse, and the reviewed table that pins the canonical homes outright.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from mill_test_support import (  # noqa: E402
    AGENTIC_CODING,
    CACHE_STAMPEDE,
    DB_MIGRATION,
    GRAPHQL,
    GRAPHQL_NATIVE,
    GRAPHQL_WRAP_GOAL,
    K8S,
    NEUTRAL_GOAL,
    STAMPEDE_CONTROLS,
    alias_conflict_index,
    episode,
    index_of,
)
from mill_family import (  # noqa: E402
    REASON_FOREIGN_MILL_ID_PREFIX,
    REVIEWED_MILL_PREFIX_HOMES,
)


class MillPrefixResolution(unittest.TestCase):
    def test_a_prefix_used_only_in_one_factory_is_native(self):
        """An unreviewed alias used in one factory is native, not a mix."""
        mills = index_of(
            (
                DB_MIGRATION,
                [
                    episode("dbm-r01-backfill", "repair backfill ordering", DB_MIGRATION),
                    episode("dbm-r02-preflight", "repair preflight ordering", DB_MIGRATION),
                    episode("zzq-r03-rollback", "repair rollback ordering", DB_MIGRATION),
                ],
            ),
        )
        identity = mills._declared_identity()
        self.assertEqual(
            mills._prefix_homes(identity)["zzq"],
            frozenset({DB_MIGRATION}),
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
                f"Fix {GRAPHQL_WRAP_GOAL}",
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
        mills, native_alias, stray_aliases = alias_conflict_index("dmr", 9)

        prefix_findings = {
            item.record_id: item
            for item in mills.findings()
            if REASON_FOREIGN_MILL_ID_PREFIX in item.reason_codes
        }
        self.assertNotIn(native_alias["id"], prefix_findings)
        for stray_alias in stray_aliases:
            self.assertEqual(
                prefix_findings[stray_alias["id"]].home_factories,
                (DB_MIGRATION,),
            )
        self.assertEqual(mills.ownership_context()["unresolved_prefixes"], [])

    def test_unknown_alias_conflict_is_not_resolved_from_destination_purity(self):
        mills, native_alias, stray_aliases = alias_conflict_index("xyz", 1)

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
                [episode("xyz-r20-unknown", NEUTRAL_GOAL, CACHE_STAMPEDE)],
            ),
            (
                K8S,
                [episode("kcl-r01-native", NEUTRAL_GOAL, K8S)],
            ),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertFalse(context["complete"])
        self.assertEqual(context["unresolved_prefixes"], ["xyz"])

    def test_the_canonical_coding_prefix_is_a_reviewed_home(self):
        """prompts/04-agentic-coding-trajectory-factory.md specifies
        ``act-rNN-<slug>-<hash>`` as that factory's canonical id shape, and the
        published corpus emits exactly that. The prefix was missing from the
        reviewed table, which is pinned here so the table cannot silently lose
        it again (Codex #96)."""
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES["act"], AGENTIC_CODING)

    def test_a_registry_verified_coding_run_can_authorize_output(self):
        """``act`` was absent from the reviewed homes, so _unresolved_prefixes
        reported it for every normal source including that factory, leaving
        context_complete false and --out refusing an otherwise clean full-run
        curation even though the directory is registry-verified and every
        payload declaration matches (Codex #96)."""
        mills = index_of(
            (
                AGENTIC_CODING,
                [
                    episode(
                        f"act-r0{index}-fix-failing-test",
                        "fix the failing pytest assertion",
                        AGENTIC_CODING,
                    )
                    for index in (2, 3, 4)
                ],
            ),
            (
                CACHE_STAMPEDE,
                [
                    episode(
                        f"cst-r0{index}-ttl-expiry",
                        "singleflight ttl expiry stampede refills",
                        CACHE_STAMPEDE,
                    )
                    for index in (1, 2)
                ],
            ),
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertEqual(context["unresolved_prefixes"], [])
        self.assertTrue(context["complete"])

    def test_a_coding_prefix_outside_its_home_is_still_foreign(self):
        """Pinning the home is what makes the prefix evidence: an act- record
        sitting in another factory must still be reported, not blessed."""
        mills = index_of(
            (
                AGENTIC_CODING,
                [
                    episode(
                        f"act-r0{index}-fix-failing-test",
                        "fix the failing pytest assertion",
                        AGENTIC_CODING,
                    )
                    for index in (2, 3)
                ],
            ),
            (
                CACHE_STAMPEDE,
                [episode("act-r04-stray", NEUTRAL_GOAL, CACHE_STAMPEDE)],
            ),
        )

        prefix_findings = [
            item
            for item in mills.findings()
            if REASON_FOREIGN_MILL_ID_PREFIX in item.reason_codes
        ]
        self.assertEqual([item.record_id for item in prefix_findings], ["act-r04-stray"])
        self.assertEqual(prefix_findings[0].home_factories, (AGENTIC_CODING,))


if __name__ == "__main__":
    unittest.main()
