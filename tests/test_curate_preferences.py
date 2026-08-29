#!/usr/bin/env python3
"""Focused tests for conservative same-context preference curation.

Covers one record at a time (``CuratePreferenceRecord``) and whole-source
scan/curate runs (``CuratePreferenceSource``). The leftover-mill quarantine
lane is in ``tests/test_curate_preferences_quarantine.py`` and the
nineteen-pair purity regression is in ``tests/test_preference_purity.py``.
"""

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _path in (REPO / "tests", REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import curate_preferences  # noqa: E402
import training_audit  # noqa: E402

from preference_pair_helpers import pair, write_jsonl  # noqa: E402


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
        source["chosen"]["state"]["agent"] = {
            "gate_memory": {"policy": "v3", "lesson": "consumed"}
        }
        source["rejected"]["state"]["agent"] = {
            "gate_memory": {"policy": "v2", "lesson": "frozen"}
        }

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
    def test_source_run_emits_manifest_and_strict_audit_pure_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            destination.mkdir()

            pure = pair("pure")
            repairable = pair("repair")
            repairable["chosen"]["state"]["identity_note"] = (
                "IDENTICAL to rejected.state — annotation"
            )
            excluded = pair("excluded")
            excluded["rejected"]["proposed_action"]["action"] = "different"
            non_preference = {"id": "ordinary", "state": {}}
            source_path = source / "preferences.jsonl"
            write_jsonl(source_path, [pure, repairable, excluded, non_preference])

            run = curate_preferences.curate_source(source)
            output = destination / "preferences.jsonl"
            manifest = destination / "manifest.jsonl"
            curate_preferences.write_run(run, source, output, manifest)

            self.assertEqual(run.summary["preference_records"], 3)
            self.assertEqual(run.summary["impure_pairs"], 2)
            self.assertEqual(run.summary["retained_pairs"], 2)
            self.assertEqual(run.summary["excluded_pairs"], 1)
            self.assertEqual(run.summary["skipped_non_preference_records"], 1)
            self.assertEqual(run.summary["retained_context_purity_pct"], 100.0)

            emitted = [json.loads(line) for line in output.read_text().splitlines()]
            entries = [json.loads(line) for line in manifest.read_text().splitlines()]
            self.assertEqual(len(emitted), 2)
            self.assertEqual(len(entries), 3)
            self.assertTrue(
                all(curate_preferences.context_is_pure(item) for item in emitted)
            )
            self.assertEqual(entries[1]["source_path"], "preferences.jsonl")
            self.assertEqual(entries[1]["source_line"], 2)
            self.assertEqual(
                entries[1]["source_sha256"],
                hashlib.sha256(source_path.read_bytes().splitlines()[1]).hexdigest(),
            )
            self.assertIsNone(entries[2]["output_sha256"])

            audit_root = root / "audit"
            audit_factory = audit_root / "failure-as-fuel-preference-cascade"
            audit_factory.mkdir(parents=True)
            (audit_factory / "preferences.jsonl").write_bytes(output.read_bytes())
            audit = training_audit.audit_run(audit_root)
            self.assertEqual(audit["preferences"]["pairs"], 2)
            self.assertEqual(audit["preferences"]["same_context"], 2)
            self.assertEqual(audit["preferences"]["context_purity_pct"], 100.0)

    def test_writer_refuses_existing_or_source_nested_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            destination.mkdir()
            write_jsonl(source / "preferences.jsonl", [pair()])
            run = curate_preferences.curate_source(source)

            existing = destination / "existing.jsonl"
            existing.write_text("sentinel\n")
            with self.assertRaisesRegex(
                curate_preferences.PreferenceCurationError, "refusing overwrite"
            ):
                curate_preferences.write_run(
                    run, source, existing, destination / "manifest.jsonl"
                )
            self.assertEqual(existing.read_text(), "sentinel\n")

            with self.assertRaisesRegex(
                curate_preferences.PreferenceCurationError, "inside source"
            ):
                curate_preferences.write_run(
                    run,
                    source,
                    source / "curated.jsonl",
                    destination / "other-manifest.jsonl",
                )

    def test_invalid_utf8_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "bad.jsonl"
            source.write_bytes(b'{"chosen":"\xff","rejected":{}}\n')

            with self.assertRaisesRegex(
                curate_preferences.PreferenceCurationError, "invalid UTF-8"
            ):
                curate_preferences.curate_source(source)


if __name__ == "__main__":
    unittest.main()
