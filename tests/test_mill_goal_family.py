#!/usr/bin/env python3
"""What a repeated goal vocabulary betrays when every other signal is native.

The last axis: records whose id prefix and declared factory both match the
directory they sit in, convicted only because a cohort of them is written from
another mill's content vocabulary. These tests pin the conviction and, at least
as importantly, its floor -- a single cross-domain task, a thin overlap, or a
generic term two reviewed lanes share must never convict a native record.
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
    INCIDENT_RESPONSE,
    K8S,
    NEUTRAL_GOAL,
    RATE_LIMIT,
    STAMPEDE_CONTROLS,
    MillAxisAssertions,
    episode,
    finding_map,
    index_of,
    strays_against_graphql,
)
from mill_family import (  # noqa: E402
    GOAL_FAMILY_MIN_FOREIGN_TOKENS,
    REASON_FOREIGN_MILL_GOAL_FAMILY,
    REASON_FOREIGN_MILL_ID_PREFIX,
    goal_family,
)


class GoalFamilyAxis(MillAxisAssertions, unittest.TestCase):
    def test_repeated_native_prefix_foreign_goal_family_is_flagged(self):
        # Same prefix and declared factory as their neighbours; only the
        # repeated goal vocabulary betrays which mill wrote them. One such
        # record is allowed to be a legitimate cross-domain task.
        strays = [
            episode(
                f"cst-r0{index}-postgraphile-wrap",
                f"Fix {GRAPHQL_WRAP_GOAL}",
                CACHE_STAMPEDE,
            )
            for index in (5, 6)
        ]
        findings = self.assert_goal_family_home(
            strays_against_graphql(strays), strays, GRAPHQL
        )
        for stray in strays:
            # The id prefix is native, so only the goal family fires.
            self.assertEqual(findings[stray["id"]].mill_prefix, "cst")
            self.assertNotIn(
                REASON_FOREIGN_MILL_ID_PREFIX, findings[stray["id"]].reason_codes
            )

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
                INCIDENT_RESPONSE,
                episode(
                    "irc-r3807-stargz-timeout",
                    "Restore the stargz timeout after layers disappeared from the TOC",
                    INCIDENT_RESPONSE,
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
                RATE_LIMIT,
                [
                    episode(
                        f"rlb-r0{index}-native",
                        "Apply retry backoff jitter after throttling",
                        RATE_LIMIT,
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
                EMAIL_WEBHOOK,
            )
            for index in (1, 2)
        ]
        mills = index_of(
            (EMAIL_WEBHOOK, native),
            (
                RATE_LIMIT,
                [
                    episode(
                        f"rlb-r0{index}-native",
                        "Apply ratelimit throttling backoff jitter",
                        RATE_LIMIT,
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

    def test_strong_foreign_anchor_does_not_convict_singleton(self):
        singleton = episode(
            "irc-r3808-buildkit-solver-outage",
            "Restore the BuildKit cachemount exporter after a solver outage",
            INCIDENT_RESPONSE,
        )
        mills = index_of(
            (INCIDENT_RESPONSE, [singleton]),
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

        self.assert_unresolved_goal_records(mills, [singleton])

    def test_a_thin_foreign_overlap_is_not_enough(self):
        stray = episode(
            "cst-r06-unrelated",
            "Fix wrapMass",
            CACHE_STAMPEDE,
        )
        self.assertLess(len(goal_family(stray)), GOAL_FAMILY_MIN_FOREIGN_TOKENS)
        mills = strays_against_graphql([stray])
        self.assertNotIn(
            stray["id"], {finding.record_id for finding in mills.findings()}
        )

    def test_repeated_strays_cannot_teach_reviewed_goal_vocabulary(self):
        strays = [
            episode(
                f"cst-r1{index}-postgraphile-wrap",
                GRAPHQL_WRAP_GOAL,
                CACHE_STAMPEDE,
            )
            for index in range(2)
        ]
        self.assert_goal_family_home(
            strays_against_graphql(strays), strays, GRAPHQL
        )

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
        mills = strays_against_graphql([prefix_foreign, native_cross_domain])

        findings = finding_map(mills)
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
        self.assert_goal_family_home(
            strays_against_graphql(strays), strays, GRAPHQL
        )

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
        mills = strays_against_graphql(strays)

        findings = finding_map(mills)
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
                GRAPHQL_WRAP_GOAL,
                CACHE_STAMPEDE,
            )
            for index in range(3)
        ]
        graphql_records = list(GRAPHQL_NATIVE[:2]) + [
            episode(
                f"gql-r3{index}-neutral",
                NEUTRAL_GOAL,
                GRAPHQL,
            )
            for index in range(8)
        ]
        mills = index_of(
            (CACHE_STAMPEDE, strays),
            (GRAPHQL, graphql_records),
        )

        findings = self.assert_goal_family_home(mills, strays, GRAPHQL)
        for record in GRAPHQL_NATIVE[:2]:
            self.assertNotIn(record["id"], findings)
        self.assertTrue(mills.ownership_context()["complete"])

    def test_repeated_foreign_goal_is_scored_without_native_vocabulary(self):
        strays = [
            episode(
                f"cache-copy-{index}",
                GRAPHQL_WRAP_GOAL,
                CACHE_STAMPEDE,
            )
            for index in (1, 2)
        ]
        mills = index_of(
            (
                CACHE_STAMPEDE,
                [episode("cache-home", NEUTRAL_GOAL, CACHE_STAMPEDE), *strays],
            ),
            (GRAPHQL, GRAPHQL_NATIVE[:2]),
        )

        self.assert_goal_family_home(mills, strays, GRAPHQL)
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
