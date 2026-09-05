#!/usr/bin/env python3
"""Whether a run is owned well enough to write a cleaned tree.

``ownership_context`` is the export-safety verdict, and it is deliberately
harder to satisfy than ``findings``: a corpus with nothing to report can still
be unsafe to publish because some record's vocabulary belongs to a factory the
run never saw. These tests pin what completes that context, what leaves it
open, and the reference scope that says how much of the reviewed table the run
actually covered.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from mill_test_support import (  # noqa: E402
    CACHE_STAMPEDE,
    DOCKER,
    EMAIL_WEBHOOK,
    GRAPHQL,
    GRAPHQL_NATIVE,
    GRAPHQL_WRAP_GOAL,
    K8S,
    NEUTRAL_GOAL,
    STAMPEDE_CONTROLS,
    UNKNOWN_GOAL,
    MillAxisAssertions,
    add_verified,
    episode,
    index_of,
    reviewed_factory_index,
    reviewed_reference_index,
    stray_against_k8s,
)


class MillOwnershipContext(MillAxisAssertions, unittest.TestCase):
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
        context = reviewed_reference_index().ownership_context()

        self.assertTrue(context["reference_scope_complete"])
        self.assertTrue(context["complete"])
        self.assertEqual(context["unresolved_prefixes"], [])

    def test_factory_names_alone_do_not_complete_the_reference_scope(self):
        context = reviewed_factory_index().ownership_context()

        self.assertFalse(context["reference_scope_complete"])

    def test_full_reference_scope_keeps_shared_novel_goals_unresolved(self):
        mills = reviewed_reference_index()
        shared_goal = "quuxwidget corgipath zibblecache"
        shared_records = [
            episode("gql-r91-shared-novel", shared_goal, GRAPHQL),
            episode("cst-r91-shared-novel", shared_goal, CACHE_STAMPEDE),
            episode("cst-r92-shared-novel", shared_goal, CACHE_STAMPEDE),
        ]
        add_verified(mills, shared_records)

        context = self.assert_unresolved_goal_records(mills, shared_records)
        self.assertTrue(context["reference_scope_complete"])

    def test_distinct_generic_signatures_do_not_pool_cohort_support(self):
        mills = reviewed_reference_index()
        add_verified(
            mills,
            [
                episode(
                    "ewr-r91-ttl-expiry-herd",
                    "Repair TTL expiry herd in webhook delivery",
                    EMAIL_WEBHOOK,
                ),
                episode(
                    "ewr-r92-stampede-thundering-refills",
                    "Repair stampede thundering refills in webhook delivery",
                    EMAIL_WEBHOOK,
                ),
            ],
        )

        self.assertEqual(mills.findings(), ())
        context = mills.ownership_context()
        self.assertTrue(context["reference_scope_complete"])
        self.assertTrue(context["complete"])
        self.assertEqual(context["unresolved_goal_records"], [])

    def _unresolved_stray_context(self, record_id_value, goal, controls=2):
        """The context left by one stray no destination in the run can own."""
        stray = episode(record_id_value, goal, CACHE_STAMPEDE)
        return self.assert_unresolved_goal_records(
            stray_against_k8s(stray, controls), [stray]
        )

    def test_unknown_goal_vocabulary_keeps_ownership_context_incomplete(self):
        self._unresolved_stray_context("cst-r99-unregistered-family", UNKNOWN_GOAL)

    def test_native_reviewed_terms_do_not_hide_unknown_goal_vocabulary(self):
        self._unresolved_stray_context(
            "cst-r98-unknown-expiry-family",
            "TTL expiry QuuxAlpha quuxBeta quuxGamma",
            1,
        )

    def test_reviewed_goal_vocabulary_names_an_absent_home(self):
        context = self._unresolved_stray_context(
            "cst-r99-postgraphile-wrap", GRAPHQL_WRAP_GOAL
        )
        self.assertEqual(context["missing_home_factories"], [GRAPHQL])

    def test_reviewed_docker_goal_vocabulary_names_an_absent_home(self):
        context = self._unresolved_stray_context(
            "cst-r99-buildkit-family", "BuildKit cachemount exporter solver layers"
        )
        self.assertEqual(context["missing_home_factories"], [DOCKER])

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
            episode(f"cst-r6{index}-unknown", UNKNOWN_GOAL, CACHE_STAMPEDE)
            for index in range(3)
        ]
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + strays),
            (
                K8S,
                [episode("kcl-r01-native", NEUTRAL_GOAL, K8S)],
            ),
        )

        self.assert_unresolved_goal_records(mills, strays)

    def test_full_prefix_coverage_cannot_authorize_unique_novel_goal_family(self):
        mills = reviewed_reference_index()
        strays = [
            episode(f"cst-r9{index}-novel-family", UNKNOWN_GOAL, CACHE_STAMPEDE)
            for index in (1, 2)
        ]
        add_verified(mills, strays)

        context = self.assert_unresolved_goal_records(mills, strays)
        self.assertTrue(context["reference_scope_complete"])


if __name__ == "__main__":
    unittest.main()
