#!/usr/bin/env python3
"""What a payload declares about its own factory, and what that proves.

The payload axis reads ``meta.factory`` -- on the wrapper, or on both
preference sides when a legacy wrapper carries none -- and reports a record
whose own declaration disagrees with the directory it sits in. These tests also
pin the other half of that reading: a destination's identity comes from the
declarations inside it, never from its directory name, so an off-slug snapshot
cannot convict everything it holds.
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
    NEUTRAL_GOAL,
    SEARCH,
    STAMPEDE_CONTROLS,
    MillAxisAssertions,
    episode,
    index_of,
    stampede_only_index,
)
from mill_family import (  # noqa: E402
    REASON_FOREIGN_PAYLOAD_FACTORY,
    declared_factory,
    declared_factory_claims,
    summarize,
)


class PayloadFactoryAxis(MillAxisAssertions, unittest.TestCase):
    def test_a_foreign_declared_factory_is_flagged(self):
        stray = episode(
            "cst-r04-stray-declaration",
            "Resolve TTL expiry thundering herd with singleflight",
            DOCKER,
        )
        finding = self.assert_declared_factory_finding(
            stampede_only_index(stray), stray, DOCKER
        )
        self.assertEqual(finding.expected_factory, CACHE_STAMPEDE)

    def test_side_stamped_preference_claims_are_resolved(self):
        """Codex #96 P1: a legacy wrapper attests its factory on both sides.

        ``curate_identity._payload_factory`` accepts a preference whose
        ``meta.factory`` lives on ``chosen``/``rejected`` rather than the
        wrapper. Reading only the wrapper left such a record with no
        declaration at all, so a destination-stamped prefix and a
        stopword-only goal made it pass as owned.
        """

        stray = {
            "id": "cst-r05-side-stamped-preference",
            "goal": NEUTRAL_GOAL,
            "chosen": {"goal": NEUTRAL_GOAL, "meta": {"factory": DOCKER}},
            "rejected": {"goal": NEUTRAL_GOAL, "meta": {"factory": DOCKER}},
        }
        self.assertIsNone(stray.get("meta"))
        self.assertEqual(declared_factory(stray), DOCKER)
        self.assertEqual(declared_factory_claims(stray), (DOCKER,))

        finding = self.assert_declared_factory_finding(
            stampede_only_index(stray), stray, DOCKER
        )
        self.assertEqual(finding.expected_factory, CACHE_STAMPEDE)

    def test_contradicting_preference_claims_are_not_ownership_evidence(self):
        """A wrapper claim that contradicts its sides names no owner."""

        contradictory = {
            "id": "cst-r06-contradicting-claims",
            "goal": NEUTRAL_GOAL,
            "chosen": {"goal": NEUTRAL_GOAL, "meta": {"factory": DOCKER}},
            "rejected": {"goal": NEUTRAL_GOAL, "meta": {"factory": DOCKER}},
            "meta": {"factory": CACHE_STAMPEDE, "round": 1},
        }
        # No single agreed claim, so the record cannot define ownership...
        self.assertIsNone(declared_factory(contradictory))
        self.assertEqual(
            declared_factory_claims(contradictory), (CACHE_STAMPEDE, DOCKER)
        )

        # ...and the disagreement is still reported rather than dropped.
        self.assert_declared_factory_finding(
            stampede_only_index(contradictory), contradictory, DOCKER
        )

    def test_side_stamped_claims_do_not_flag_a_matching_destination(self):
        """Agreeing side claims that name the destination stay clean."""

        native = {
            "id": "cst-r07-side-stamped-native",
            "goal": NEUTRAL_GOAL,
            "chosen": {"goal": NEUTRAL_GOAL, "meta": {"factory": CACHE_STAMPEDE}},
            "rejected": {"goal": NEUTRAL_GOAL, "meta": {"factory": CACHE_STAMPEDE}},
        }
        mills = stampede_only_index(native)
        self.assertNotIn(
            native["id"], {finding.record_id for finding in mills.findings()}
        )

    def test_declared_identity_comes_from_payloads_not_directory_names(self):
        """A snapshot directory with an off-slug name must not flag everything."""
        mills = index_of(("staging-copy", STAMPEDE_CONTROLS))
        self.assertEqual(mills.findings(), ())

    def test_tied_snapshot_identity_keeps_ownership_context_incomplete(self):
        mills = index_of(
            (
                CACHE_STAMPEDE,
                [episode("cache-home", NEUTRAL_GOAL, CACHE_STAMPEDE)],
            ),
            (
                GRAPHQL,
                [episode("graphql-home", NEUTRAL_GOAL, GRAPHQL)],
            ),
            (
                "staging-copy",
                [
                    episode("snapshot-cache", NEUTRAL_GOAL, CACHE_STAMPEDE),
                    episode("snapshot-graphql", NEUTRAL_GOAL, GRAPHQL),
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
                [episode("cache-home", NEUTRAL_GOAL, CACHE_STAMPEDE)],
            ),
            (
                GRAPHQL,
                [episode("graphql-home", NEUTRAL_GOAL, GRAPHQL)],
            ),
            (
                "staging-copy",
                [episode("snapshot-unknown", NEUTRAL_GOAL, absent)],
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
            NEUTRAL_GOAL,
            SEARCH,
        )
        mills = index_of(
            (EMAIL_WEBHOOK, [stray]),
        )

        finding = mills.findings()[0]
        self.assertEqual(finding.record_id, stray["id"])
        self.assertIn(REASON_FOREIGN_PAYLOAD_FACTORY, finding.reason_codes)
        self.assertEqual(
            finding.expected_factory, EMAIL_WEBHOOK
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
        report = summarize(stampede_only_index(stray).findings())
        self.assertEqual(
            report["by_factory"][CACHE_STAMPEDE]["foreign_prefixes"], {}
        )

    def test_preference_side_factory_stamps_feed_the_payload_axis(self):
        destination = "tool-use-preference-factory"
        foreign = "failure-as-fuel-preference-cascade"

        def pair(record_id, factory):
            return {
                "id": record_id,
                "chosen": {"meta": {"factory": factory}},
                "rejected": {"meta": {"factory": factory}},
            }

        native = pair("tup-r1-native", destination)
        stray = pair("tup-r2-foreign", foreign)
        findings = {
            finding.record_id: finding
            for finding in index_of((destination, [native, stray])).findings()
        }
        self.assertIn(stray["id"], findings)
        self.assertIn(
            REASON_FOREIGN_PAYLOAD_FACTORY,
            findings[stray["id"]].reason_codes,
        )

    def test_consistent_side_origin_beats_destination_wrapper_in_payload_axis(self):
        destination = "tool-use-preference-factory"
        foreign = "failure-as-fuel-preference-cascade"

        def pair(record_id, side_factory):
            return {
                "id": record_id,
                "meta": {"factory": destination},
                "chosen": {"meta": {"factory": side_factory}},
                "rejected": {"meta": {"factory": side_factory}},
            }

        native = pair("tup-r1-native", destination)
        stray = pair("tup-r2-foreign", foreign)
        findings = {
            finding.record_id: finding
            for finding in index_of((destination, [native, stray])).findings()
        }
        self.assertIn(stray["id"], findings)
        self.assertIn(
            REASON_FOREIGN_PAYLOAD_FACTORY,
            findings[stray["id"]].reason_codes,
        )
        self.assertEqual(findings[stray["id"]].declared_factory, foreign)

if __name__ == "__main__":
    unittest.main()
