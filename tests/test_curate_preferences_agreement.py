#!/usr/bin/env python3
"""Per-field context agreement and the publication gate it feeds."""

import tempfile
import unittest
from pathlib import Path

from preference_test_support import (  # noqa: E402
    PREFERENCE_ISOLATION_DOC,
    PURITY_FIXTURES,
    pair,
    write_jsonl,
)
import curate_preferences  # noqa: E402


class ContextFieldAgreement(unittest.TestCase):
    def test_agreement_is_reported_per_field_before_any_repair(self):
        pure = curate_preferences.curate_preference_record(pair())
        self.assertIs(pure.same_state, True)
        self.assertIs(pure.same_proposed_action, True)

        state_only = curate_preferences.curate_preference_record(
            pair(
                chosen_state={"sim_or_real": "designed", "domain": "a"},
                rejected_state={"sim_or_real": "designed", "domain": "b"},
            )
        )
        self.assertIs(state_only.same_state, False)
        self.assertIs(state_only.same_proposed_action, True)

        proposal_only = pair()
        proposal_only["rejected"]["proposed_action"] = {
            "action": "inspect-differently",
            "decision_basis": "fixture",
        }
        decision = curate_preferences.curate_preference_record(proposal_only)
        self.assertIs(decision.same_state, True)
        self.assertIs(decision.same_proposed_action, False)
        self.assertEqual(decision.reason_codes, ("PROPOSED_ACTION_CONTEXT_DIVERGES",))

    def test_repairs_report_the_source_agreement_not_their_own_output(self):
        source = pair()
        source["chosen"]["state"]["identity_note"] = "IDENTICAL to rejected.state; annotation only."
        decision = curate_preferences.curate_preference_record(source)
        self.assertEqual(decision.action, curate_preferences.ACTION_REPAIRED)
        self.assertIs(decision.same_state, False)
        self.assertIs(decision.same_proposed_action, True)
        self.assertTrue(curate_preferences.context_is_pure(decision.record))

    def test_malformed_pairs_have_undetermined_agreement(self):
        for record in ("not-an-object", {"chosen": {}, "rejected": {}}):
            decision = curate_preferences.curate_preference_record(record)
            self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
            self.assertIsNone(decision.same_state)
            self.assertIsNone(decision.same_proposed_action)
        self.assertEqual(curate_preferences.context_field_agreement("not-an-object"), (None, None))

    def test_each_field_is_measured_when_the_other_is_malformed(self):
        equal_state = pair("equal-state")
        del equal_state["rejected"]["proposed_action"]
        decision = curate_preferences.curate_preference_record(equal_state)
        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual((decision.same_state, decision.same_proposed_action), (True, None))

        divergent_state = pair(
            "divergent-state",
            chosen_state={"domain": "a"},
            rejected_state={"domain": "b"},
        )
        del divergent_state["chosen"]["proposed_action"]
        self.assertEqual(
            curate_preferences.context_field_agreement(divergent_state),
            (False, None),
        )

        equal_proposal = pair("equal-proposal")
        del equal_proposal["chosen"]["state"]
        self.assertEqual(
            curate_preferences.context_field_agreement(equal_proposal),
            (None, True),
        )

        divergent_proposal = pair("divergent-proposal")
        del divergent_proposal["rejected"]["state"]
        divergent_proposal["rejected"]["proposed_action"]["action"] = "other"
        self.assertEqual(
            curate_preferences.context_field_agreement(divergent_proposal),
            (None, False),
        )

    def test_partial_agreement_contributes_known_field_totals(self):
        malformed = pair(
            "partial",
            chosen_state={"domain": "a"},
            rejected_state={"domain": "b"},
        )
        del malformed["rejected"]["proposed_action"]
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "preferences.jsonl"
            write_jsonl(source, [malformed])
            run = curate_preferences.curate_source(source)

        self.assertEqual(run.summary["state_divergent_pairs"], 1)
        self.assertEqual(run.summary["state_undetermined_pairs"], 0)
        self.assertEqual(run.summary["proposed_action_undetermined_pairs"], 1)
        self.assertEqual(run.summary["context_undetermined_pairs"], 1)
        audit = curate_preferences.build_audit(run)
        self.assertEqual(audit["impure_pairs"][0]["divergent_context_fields"], ["state"])

    def test_non_finite_context_is_excluded_without_raising(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                record = pair("non-finite")
                record["chosen"]["state"]["level"] = value
                record["rejected"]["state"]["level"] = 1.0
                decision = curate_preferences.curate_preference_record(record)
                self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
                self.assertEqual(
                    decision.reason_codes,
                    ("PREFERENCE_RECORD_NOT_JSON_SERIALIZABLE",),
                )
                self.assertIsNone(decision.same_state)
                self.assertIs(decision.same_proposed_action, True)

    def test_undetermined_pairs_are_bucketed_and_never_dropped(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "preferences.jsonl"
            write_jsonl(source, [pair(), {"chosen": {}, "rejected": {}}])
            run = curate_preferences.curate_source(source)
            self.assertEqual(run.summary["context_undetermined_pairs"], 1)
            self.assertEqual(run.summary["impure_pairs"], 1)
            self.assertEqual(run.summary["state_divergent_pairs"], 0)
            audit = curate_preferences.build_audit(run)
            self.assertEqual(len(audit["impure_pairs"]), 1)
            self.assertEqual(audit["impure_pairs"][0]["divergent_context_fields"], [])


class PublicationGateCoversUnemittablePairs(unittest.TestCase):
    """A pure-context pair the curator cannot emit must still block publish."""

    def test_equal_context_exclusion_is_counted_as_unpublishable(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "preferences.jsonl"
            malformed = pair("equal-context-nonfinite")
            malformed["reward_delta"] = float("nan")
            write_jsonl(source, [malformed])

            summary = curate_preferences.curate_source(source).summary

        # The narrowed same-context measure stays truthful: this pair's
        # context really is equal and comparable.
        self.assertEqual(summary["impure_pairs"], 0)
        self.assertEqual(summary["excluded_pairs"], 1)
        # ...but it cannot be emitted, so the gate total sees it.
        self.assertEqual(summary["unpublishable_pairs"], 1)

    def test_impure_pairs_are_unpublishable_without_being_double_counted(self):
        summary = curate_preferences.curate_source(PURITY_FIXTURES).summary

        # Every exclusion in this corpus is a context exclusion, so the gate
        # total is the historical 19 and not 19 + 12.
        self.assertEqual(summary["preference_records"], 42)
        self.assertEqual(summary["impure_pairs"], 19)
        self.assertEqual(summary["excluded_pairs"], 12)
        self.assertEqual(summary["unpublishable_pairs"], 19)

    def test_a_clean_corpus_reports_a_zero_gate_total(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "preferences.jsonl"
            write_jsonl(source, [pair("clean-a"), pair("clean-b")])

            summary = curate_preferences.curate_source(source).summary

        self.assertEqual(summary["retained_pairs"], 2)
        self.assertEqual(summary["unpublishable_pairs"], 0)

    def test_the_documented_gate_names_the_field_that_blocks_both_defects(self):
        doc = PREFERENCE_ISOLATION_DOC.read_text(encoding="utf-8")

        self.assertIn("summary.unpublishable_pairs", doc)
        self.assertIn(
            "# purity gate: summary.unpublishable_pairs must be 0", doc
        )


if __name__ == "__main__":
    unittest.main()
