#!/usr/bin/env python3
"""Conservative same-context curation of one preference record and one source."""

import copy
import tempfile
import unittest
from pathlib import Path

from preference_test_support import (  # noqa: E402
    pair,
    write_jsonl,
)
import curate_preferences  # noqa: E402
import training_audit  # noqa: E402


class CuratePreferenceRecord(unittest.TestCase):
    def test_pure_pair_is_retained_without_mutating_input(self):
        source = pair()
        before = copy.deepcopy(source)

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_RETAINED)
        self.assertEqual(decision.record, source)
        self.assertIsNot(decision.record, source)
        self.assertEqual(source, before)
        self.assertTrue(curate_preferences.context_is_pure(decision.record))

    def test_identity_note_only_difference_copies_exact_reference(self):
        source = pair()
        source["chosen"]["state"]["identity_note"] = (
            "IDENTICAL to rejected.state — this annotation is not model context"
        )
        source["chosen"]["proposed_action"]["identity_note"] = (
            "IDENTICAL to rejected.proposed_action — gate is the free variable"
        )
        exact_state = copy.deepcopy(source["rejected"]["state"])
        exact_proposal = copy.deepcopy(source["rejected"]["proposed_action"])

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_REPAIRED)
        self.assertEqual(decision.classification, "attested_identity_annotation_only")
        self.assertEqual(decision.record["chosen"]["state"], exact_state)
        self.assertEqual(decision.record["rejected"]["state"], exact_state)
        self.assertEqual(decision.record["chosen"]["proposed_action"], exact_proposal)
        self.assertTrue(curate_preferences.context_is_pure(decision.record))

    def test_identity_note_is_not_trusted_when_other_context_also_changes(self):
        source = pair()
        source["chosen"]["state"].update(
            {
                "identity_note": "IDENTICAL to rejected.state — unsupported claim",
                "temperature_c": 42,
            }
        )
        source["rejected"]["state"]["temperature_c"] = 21

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertIn("STATE_CONTEXT_DIVERGES", decision.reason_codes)
        self.assertIsNone(decision.record)

    def test_attested_proposal_annotation_copies_exact_reference(self):
        source = pair(
            proposal={
                "action": "route load",
                "decision_basis": "fixture",
                "source": "base policy (standard flow)",
                "snn_readout": {"margin": 0.2, "note": "reference annotation"},
            }
        )
        source["chosen"]["proposed_action"]["source"] = (
            "base policy (standard flow) — IDENTICAL proposal to the rejected branch; "
            "gate is the only free variable"
        )
        source["chosen"]["proposed_action"]["snn_readout"]["note"] = (
            "same poisoned prior; explanatory chosen-side annotation"
        )
        exact_reference = copy.deepcopy(source["rejected"]["proposed_action"])

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_REPAIRED)
        self.assertEqual(decision.classification, "attested_proposal_annotation_only")
        self.assertEqual(decision.record["chosen"]["proposed_action"], exact_reference)
        self.assertTrue(curate_preferences.context_is_pure(decision.record))

    def test_semantically_different_proposals_are_excluded_despite_identity_words(self):
        source = pair()
        source["chosen"]["proposed_action"] = {
            "action": "conditional accept",
            "source": "new policy — IDENTICAL proposal to the rejected branch",
        }
        source["rejected"]["proposed_action"] = {
            "action": "bare accept",
            "source": "old policy",
        }

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual(decision.reason_codes, ("PROPOSED_ACTION_CONTEXT_DIVERGES",))

    def test_non_attesting_identity_note_text_is_excluded(self):
        source = pair()
        source["chosen"]["state"]["identity_note"] = (
            "chosen branch observed a DIFFERENT sensor bias than rejected"
        )

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual(decision.reason_codes, ("STATE_CONTEXT_DIVERGES",))
        self.assertIsNone(decision.record)

    def test_identity_note_naming_a_longer_field_cannot_authorize_a_repair(self):
        # "rejected.stateful" merely begins with "rejected.state"; it is a
        # claim about a different field, and an explicit denial at that.
        source = pair()
        source["chosen"]["state"]["identity_note"] = (
            "IDENTICAL to rejected.stateful context is actually different"
        )

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertIsNone(decision.record)

    def test_identity_note_naming_a_deeper_path_cannot_authorize_a_repair(self):
        source = pair()
        source["chosen"]["state"]["identity_note"] = (
            "IDENTICAL to rejected.state.sim_or_real only"
        )

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertIsNone(decision.record)

    def test_proposal_marker_naming_a_longer_branch_cannot_authorize_a_repair(self):
        source = pair(
            proposal={
                "action": "route load",
                "decision_basis": "fixture",
                "source": "base policy (standard flow)",
                "snn_readout": {"margin": 0.2, "note": "reference annotation"},
            }
        )
        # "rejected branching" is not a claim about the rejected branch.
        source["chosen"]["proposed_action"]["source"] = (
            "base policy (standard flow) — IDENTICAL proposal to the "
            "rejected branching was explored separately"
        )

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertIsNone(decision.record)

    def test_identity_note_attesting_the_wrong_side_is_excluded(self):
        source = pair()
        source["chosen"]["state"]["identity_note"] = (
            "IDENTICAL to chosen.state — attests the attesting side itself"
        )

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual(decision.reason_codes, ("STATE_CONTEXT_DIVERGES",))

    def test_proposal_source_diff_without_identity_marker_is_excluded(self):
        source = pair(
            proposal={
                "action": "route load",
                "decision_basis": "fixture",
                "source": "policy v1 (frozen)",
            }
        )
        source["chosen"]["proposed_action"]["source"] = "policy v2 (retrained)"

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual(decision.reason_codes, ("PROPOSED_ACTION_CONTEXT_DIVERGES",))
        self.assertIsNone(decision.record)

    def test_loosely_equal_cross_type_context_values_are_excluded(self):
        # True == 1 and 42 == 42.0 under Python ==, but the canonical context
        # differs; the strict type guard must treat these as divergence.
        boolean_pair = pair()
        boolean_pair["chosen"]["state"]["flag"] = True
        boolean_pair["rejected"]["state"]["flag"] = 1
        numeric_pair = pair()
        numeric_pair["chosen"]["state"]["reading"] = 42
        numeric_pair["rejected"]["state"]["reading"] = 42.0

        for source in (boolean_pair, numeric_pair):
            decision = curate_preferences.curate_preference_record(source)
            self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
            self.assertEqual(decision.reason_codes, ("STATE_CONTEXT_DIVERGES",))
            self.assertFalse(curate_preferences.context_is_pure(source))

    def test_branch_specific_gate_version_state_is_excluded(self):
        source = pair()
        source["chosen"]["state"].update(
            {"episode_id": "chosen", "note": "same day; gate v2.5 in service"}
        )
        source["rejected"]["state"].update(
            {"episode_id": "rejected", "note": "same day; gate v2.4 in service"}
        )

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual(
            decision.reason_codes,
            ("BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE",),
        )

    def test_policy_memory_difference_is_excluded(self):
        source = pair()
        source["chosen"]["state"]["agent"] = {"gate_memory": {"policy": "v3", "lesson": "consumed"}}
        source["rejected"]["state"]["agent"] = {"gate_memory": {"policy": "v2", "lesson": "frozen"}}

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual(decision.reason_codes, ("POLICY_MEMORY_CONTEXT_DIVERGES",))

    def test_repair_is_record_idempotent(self):
        source = pair()
        source["chosen"]["state"]["identity_note"] = "IDENTICAL to rejected.state"
        first = curate_preferences.curate_preference_record(source)
        second = curate_preferences.curate_preference_record(first.record)

        self.assertEqual(first.action, curate_preferences.ACTION_REPAIRED)
        self.assertEqual(second.action, curate_preferences.ACTION_RETAINED)
        self.assertEqual(first.record, second.record)

    def test_missing_context_is_explicitly_excluded(self):
        source = {"id": "bad", "chosen": {}, "rejected": {}, "reward_delta": {}}

        decision = curate_preferences.curate_preference_record(source)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual(
            decision.reason_codes,
            ("PREFERENCE_CONTEXT_MISSING_OR_INVALID",),
        )

    def test_non_finite_context_is_excluded_with_a_reason_code(self):
        diverging = pair("nan-diverging")
        diverging["chosen"]["state"]["level"] = float("nan")
        diverging["rejected"]["state"]["level"] = 1.0

        decision = curate_preferences.curate_preference_record(diverging)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual(
            decision.reason_codes, ("PREFERENCE_RECORD_NOT_JSON_SERIALIZABLE",)
        )
        self.assertIsNone(decision.record)

    def test_non_finite_context_is_not_retained_just_because_both_sides_match(self):
        # ``inf == inf`` makes the two sides compare equal path-by-path, but the
        # pair still cannot be written as JSON, so it must not be retained.
        matching = pair("inf-matching")
        for side in ("chosen", "rejected"):
            matching[side]["state"]["level"] = float("inf")

        decision = curate_preferences.curate_preference_record(matching)

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual(
            decision.reason_codes, ("PREFERENCE_RECORD_NOT_JSON_SERIALIZABLE",)
        )

    def test_lane_purity_gate_agrees_with_the_strict_audit_invariant(self):
        pure = pair("agree-pure")
        state_drift = pair("agree-state", rejected_state={"sim_or_real": "designed"})
        proposal_drift = pair("agree-proposal")
        proposal_drift["rejected"]["proposed_action"]["action"] = "other"
        missing = {"id": "agree-missing", "chosen": {}, "rejected": {}}

        for record in (pure, state_drift, proposal_drift, missing):
            with self.subTest(record=record["id"]):
                audit = training_audit.preference_context_purity(
                    record, record["chosen"], record["rejected"]
                )
                self.assertFalse(audit["episode_pair"])
                self.assertEqual(
                    curate_preferences.context_is_pure(record), audit["pure"]
                )


class CuratePreferenceSource(unittest.TestCase):
    """Scan behaviour this module owns.

    Source scanning and the writer's destination guards are the subject of
    ``test_curate_preferences_writer``; the three tests that used to sit here
    were exact duplicates of tests already living there.
    """

    def test_non_finite_records_do_not_abort_the_source_scan(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "preferences.jsonl"
            records = [pair("good")]
            for index, value in enumerate((float("nan"), float("inf"), float("-inf")), 1):
                record = pair(f"bad-{index}")
                record["chosen"]["state"]["level"] = value
                records.append(record)
            write_jsonl(source, records)

            run = curate_preferences.curate_source(source)

        self.assertEqual(run.summary["preference_records"], 4)
        self.assertEqual(run.summary["retained_pairs"], 1)
        self.assertEqual(run.summary["excluded_pairs"], 3)
        self.assertEqual(
            run.summary["reason_codes"]["PREFERENCE_RECORD_NOT_JSON_SERIALIZABLE"],
            3,
        )
        self.assertEqual([entry["action"] for entry in run.manifest[1:]], ["excluded"] * 3)


if __name__ == "__main__":
    unittest.main()
