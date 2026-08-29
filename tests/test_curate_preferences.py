#!/usr/bin/env python3
"""Conservative same-context curation of one preference record and one source."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from preference_test_support import (  # noqa: E402
    PREFERENCE_ISOLATION_DOC,
    PURITY_FIXTURES,
    leftover_mill_episode,
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


class LeftoverMillQuarantine(unittest.TestCase):
    """Leftover-mill records are excluded and named, never silently dropped."""

    def _run(self, records):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            source.mkdir()
            write_jsonl(source / "batch-r723.jsonl", records)
            return curate_preferences.curate_source(source)

    def test_episode_in_a_preference_tree_is_quarantined_not_counted(self):
        run = self._run(
            [
                leftover_mill_episode("dbc-r723-buildah-layers-vfs-id-leftover"),
                pair("crp-r723-real-pair"),
            ]
        )

        summary = run.summary
        self.assertEqual(summary["json_records_seen"], 2)
        self.assertEqual(summary["preference_records"], 1)
        self.assertEqual(summary["skipped_non_preference_records"], 1)
        self.assertEqual(summary["leftover_mill_records"], 1)
        self.assertEqual(summary["leftover_mill_kinds"], {"episode": 1})
        # The pair denominator never absorbs the mill record.
        self.assertEqual(summary["retained_pairs"], 1)
        self.assertEqual(len(run.records), 1)
        self.assertEqual(run.records[0]["id"], "crp-r723-real-pair")

        quarantined = [
            entry
            for entry in run.manifest
            if entry["action"] == curate_preferences.ACTION_QUARANTINED
        ]
        self.assertEqual(len(quarantined), 1)
        entry = quarantined[0]
        self.assertEqual(entry["source_path"], "batch-r723.jsonl")
        self.assertEqual(entry["source_line"], 1)
        self.assertEqual(entry["source_record_id"], "dbc-r723-buildah-layers-vfs-id-leftover")
        self.assertEqual(entry["classification"], "leftover_mill_episode")
        self.assertEqual(entry["reason_codes"], ["LEFTOVER_MILL_KIND_MIX"])
        self.assertIsNone(entry["output_id"])
        self.assertIsNone(entry["output_sha256"])

    def test_episode_with_reward_delta_still_bypasses_pair_denominator(self):
        episode = leftover_mill_episode("dbc-r723-buildah-layers-vfs-id-leftover")
        episode["reward_delta"] = 0.4
        run = self._run([episode])

        self.assertEqual(run.summary["preference_records"], 0)
        self.assertEqual(run.summary["skipped_non_preference_records"], 1)
        self.assertEqual(run.summary["leftover_mill_records"], 1)
        self.assertEqual(run.summary["actions"], {})
        self.assertEqual(len(run.manifest), 1)
        self.assertEqual(
            run.manifest[0]["action"],
            curate_preferences.ACTION_QUARANTINED,
        )
        self.assertEqual(
            run.manifest[0]["transform"],
            {
                "name": "same-context-preference-curation",
                "version": "1.2.0",
            },
        )
        self.assertEqual(run.summary["transform"], run.manifest[0]["transform"])

    def test_unclassifiable_skips_are_not_reported_as_leftover_mill(self):
        run = self._run([{"id": "ordinary", "state": {}}, pair("crp-r723-real-pair")])

        self.assertEqual(run.summary["skipped_non_preference_records"], 1)
        self.assertEqual(run.summary["leftover_mill_records"], 0)
        self.assertEqual(run.summary["leftover_mill_kinds"], {})
        self.assertEqual(
            [entry["action"] for entry in run.manifest],
            [curate_preferences.ACTION_RETAINED],
        )

    def test_public_audit_excludes_quarantine_rows(self):
        run = self._run(
            [
                leftover_mill_episode("dbc-r723-buildah-vfs-audit-leftover"),
                pair("crp-r723-real-pair"),
            ]
        )

        audit = curate_preferences.build_audit(run)
        self.assertEqual(audit["summary"]["preference_pairs"], 1)
        self.assertEqual(audit["summary"]["impure_pairs"], 0)
        self.assertEqual(audit["impure_pairs"], [])
        self.assertEqual(audit["transform"]["version"], "1.2.0")

    def test_human_report_names_the_quarantined_count(self):
        run = self._run(
            [
                leftover_mill_episode("dbc-r723-buildah-vfs-graphroot-leftover"),
                pair("crp-r723-real-pair"),
            ]
        )
        report = curate_preferences._render_human(run)
        self.assertIn("Leftover mill (quarantined): 1", report)
        self.assertIn("quarantined [LEFTOVER_MILL_KIND_MIX]", report)


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
            self.assertTrue(all(curate_preferences.context_is_pure(item) for item in emitted))
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
                curate_preferences.write_run(run, source, existing, destination / "manifest.jsonl")
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
