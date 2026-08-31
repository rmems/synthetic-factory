#!/usr/bin/env python3
"""The isolation attestation, and the shared-context purity it delegates."""

import copy
import unittest

from preference_arms_support import (  # noqa: E402
    SINGLE_SESSION,
    TWO_SESSION_ROUND,
    check,
    first,
    run_cli,
)
import preference_arms  # noqa: E402


class IsolationAttestation(unittest.TestCase):
    def test_single_session_attestation_is_rejected(self):
        scan = preference_arms.scan_source(SINGLE_SESSION)
        self.assertTrue(scan.blocked)
        decision = scan.decisions[0]
        self.assertEqual(decision.isolation, "single-session")
        self.assertEqual(decision.reason_codes, (preference_arms.REASON_SINGLE_SESSION,))
        self.assertGreater(decision.arm_distance, preference_arms.DEFAULT_MIN_ARM_DISTANCE)

    def test_legacy_scan_reports_but_does_not_block_on_attestation(self):
        scan = preference_arms.scan_source(
            SINGLE_SESSION, preference_arms.GatePolicy(require_isolation=False)
        )
        self.assertFalse(scan.blocked)
        self.assertEqual(scan.decisions[0].isolation, "single-session")
        self.assertEqual(scan.summary["two_session_pairs"], 0)

    def test_cli_flag_relaxes_the_attestation(self):
        code, _, _ = run_cli(["scan", str(SINGLE_SESSION)])
        self.assertEqual(code, 1)
        code, _, _ = run_cli(["scan", str(SINGLE_SESSION), "--no-require-isolation"])
        self.assertEqual(code, 0)

    def test_undeclared_isolation_is_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        for holder in (record, record["chosen"], record["rejected"]):
            holder["meta"].pop("isolation", None)
        decision = check(record)
        self.assertIsNone(decision.isolation)
        self.assertEqual(
            decision.reason_codes,
            (preference_arms.REASON_ISOLATION_UNDECLARED,),
        )

    def test_conflicting_declarations_are_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"]["meta"]["isolation"] = "single-session"
        decision = check(record)
        self.assertEqual(decision.isolation, "single-session|two-session")
        self.assertEqual(
            decision.reason_codes,
            (preference_arms.REASON_ISOLATION_CONFLICT,),
        )

    def test_arm_only_declaration_is_accepted(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["meta"].pop("isolation")
        self.assertEqual(check(record).reason_codes, ())

    def test_non_object_meta_is_treated_as_no_declaration(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["meta"] = "two-session"
        record["chosen"]["meta"] = None
        record["rejected"]["meta"] = ["two-session"]
        decision = check(record)
        self.assertIsNone(decision.isolation)
        self.assertEqual(
            decision.reason_codes,
            (preference_arms.REASON_ISOLATION_UNDECLARED,),
        )

    def assert_untrusted_isolation(self, **kwargs):
        """The record's own attestation cannot satisfy a trusted-marker check."""
        decision = check(first(TWO_SESSION_ROUND), **kwargs)
        self.assertIn(preference_arms.REASON_ISOLATION_UNTRUSTED, decision.reason_codes)

    def test_record_attestation_is_not_a_trusted_publication_marker(self):
        self.assert_untrusted_isolation(require_trusted_isolation=True)

    def test_publisher_controlled_two_session_marker_clears_the_gate(self):
        scan = preference_arms.scan_source(
            TWO_SESSION_ROUND,
            preference_arms.GatePolicy(
                trusted_isolation=preference_arms.TWO_SESSION,
                require_trusted_isolation=True,
            ),
        )
        self.assertFalse(scan.blocked)
        self.assertEqual(scan.summary["trusted_two_session_pairs"], 3)

    def test_relabelled_record_cannot_override_a_conflicting_publisher_marker(self):
        self.assert_untrusted_isolation(
            trusted_isolation="single-session",
            require_trusted_isolation=True,
        )


class ContextPurityIsDelegatedAndEnforced(unittest.TestCase):
    def test_state_drift_is_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"]["state"]["environment"]["observed_c"] = -70.0
        decision = check(record)
        self.assertFalse(decision.same_context)
        self.assertIn(preference_arms.REASON_CONTEXT_DIVERGES, decision.reason_codes)

    def test_proposal_drift_is_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"]["proposed_action"]["arguments"]["silence_minutes"] = 5
        decision = check(record)
        self.assertFalse(decision.same_context)
        self.assertIn(preference_arms.REASON_CONTEXT_DIVERGES, decision.reason_codes)

    def test_malformed_pair_is_reported_once(self):
        decision = check({"id": "broken", "chosen": "not an object", "rejected": {}})
        self.assertEqual(decision.reason_codes, (preference_arms.REASON_MALFORMED,))
        self.assertIsNone(decision.arm_distance)

    def test_arm_gate_inherits_the_canonical_spelling_rule(self):
        # Same-context purity is canonical equality, not value equality: both
        # arms copy this subtree from the one Shared context block, so 9
        # against 9.0 means they did not copy from a single source. The
        # strict-audit corpus owns this rule; the arm gate delegates to it and
        # must not soften it into `float(a) == float(b)`.
        for chosen_value, rejected_value in ((9, 9.0), (9.0, 9), (True, 1), (0, 0.0)):
            with self.subTest(chosen=chosen_value, rejected=rejected_value):
                record = copy.deepcopy(first(TWO_SESSION_ROUND))
                record["chosen"]["state"]["environment"]["door_cycles"] = chosen_value
                record["rejected"]["state"]["environment"]["door_cycles"] = rejected_value
                decision = check(record)
                self.assertFalse(decision.same_context)
                self.assertIn(preference_arms.REASON_CONTEXT_DIVERGES, decision.reason_codes)

    def test_one_shared_spelling_is_pure(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        for side in ("chosen", "rejected"):
            record[side]["state"]["environment"]["door_cycles"] = 9.0
        self.assertTrue(check(record).same_context)

if __name__ == "__main__":
    unittest.main()
