#!/usr/bin/env python3
"""Focused tests for conservative same-context preference curation."""

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import curate_preferences  # noqa: E402
import training_audit  # noqa: E402

PURITY_FIXTURES = REPO / "tests" / "fixtures" / "preference-purity"

# Golden digests of the committed fixture corpus. Pinned as constants (not
# captured at runtime) so an in-place rewrite of the fixtures by the code
# under test — even an idempotent one performed before the immutability test
# takes its baseline — fails loudly instead of self-verifying.
GOLDEN_FIXTURE_SHA256 = {
    "batch-r02.jsonl": "9f85fd74e6974f91fbc9e6a59b4189e2cd93fdd4aaf12c081460132947aefdcc",
    "batch-r03.jsonl": "df8bc117a6e9347e9c8cf71ec3f408c7c36a49d708be1d9ea0d0d6ced5ecbd67",
    "batch-r04.jsonl": "60cf07294147cce075287ec468bbbec93a188b1508766bbdf2515686f90480fb",
    "batch-r05.jsonl": "6baf5f651c03da46fcbe4e9fd057d1f27eed97701d303847bcb2ccb2721818cc",
    "batch-r06.jsonl": "cb6cace4b68f20333809fe63ece0994c4744d3b92a926d689b819636203e3edf",
    "batch-r07.jsonl": "c63f8a1fb02fe88a394495c0b85635df43c0860fcc52f8a6724e598fcfff287e",
    "batch-r08.jsonl": "5741c3bdcc276972bdaefc6d2c1734beea579c5416782f47ea3e60ba6a8769d1",
    "batch-r09.jsonl": "9aa62ca8bd273869c994c4370839dfcbef115d53bad9637b4511a5c3cc02b6e5",
    "batch-r10.jsonl": "43e91b9967322aeeae3a06bb1fb9c6c806731f39c56ec389bb5fc28c0610570b",
    "preferences.jsonl": "12b0062d4a2d3f7494979bfda863401abf8faa26ab3ade426b6bfda94cdd0cff",
}

# The nineteen impure pairs, keyed by (file, line), mirroring the read-only
# scan of the real raw corpus (outputs/raw/2026-08-17/
# failure-as-fuel-preference-cascade, 2026-08-19): action, classification,
# and reason codes are identical to the raw decisions line-for-line.
REPAIRED_IDENTITY = (
    "repaired",
    "attested_identity_annotation_only",
    (
        "EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE",
        "BRANCH_ONLY_IDENTITY_NOTE_REMOVED",
    ),
)
EXPECTED_IMPURE_DECISIONS = {
    ("batch-r02.jsonl", 1): (
        "excluded",
        "unsupported_context_divergence",
        ("BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE",),
    ),
    ("batch-r02.jsonl", 2): (
        "excluded",
        "unsupported_context_divergence",
        ("BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE",),
    ),
    ("batch-r02.jsonl", 3): (
        "excluded",
        "unsupported_context_divergence",
        ("BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE",),
    ),
    ("batch-r03.jsonl", 4): REPAIRED_IDENTITY,
    ("batch-r03.jsonl", 5): REPAIRED_IDENTITY,
    ("batch-r03.jsonl", 6): REPAIRED_IDENTITY,
    ("batch-r04.jsonl", 4): REPAIRED_IDENTITY,
    ("batch-r04.jsonl", 5): REPAIRED_IDENTITY,
    ("batch-r04.jsonl", 6): REPAIRED_IDENTITY,
    ("batch-r05.jsonl", 2): (
        "excluded",
        "unsupported_context_divergence",
        ("PROPOSED_ACTION_CONTEXT_DIVERGES",),
    ),
    ("batch-r05.jsonl", 3): (
        "repaired",
        "attested_proposal_annotation_only",
        (
            "EXACT_PROPOSAL_COPIED_FROM_ATTESTED_REFERENCE",
            "BRANCH_ONLY_PROPOSAL_ANNOTATION_REMOVED",
        ),
    ),
    ("batch-r06.jsonl", 2): (
        "excluded",
        "unsupported_context_divergence",
        ("POLICY_MEMORY_CONTEXT_DIVERGES",),
    ),
    ("batch-r07.jsonl", 2): (
        "excluded",
        "unsupported_context_divergence",
        ("POLICY_MEMORY_CONTEXT_DIVERGES",),
    ),
    **{
        ("preferences.jsonl", line): (
            "excluded",
            "unsupported_context_divergence",
            ("STATE_CONTEXT_DIVERGES", "PROPOSED_ACTION_CONTEXT_DIVERGES"),
        )
        for line in range(1, 7)
    },
}


def trajectory(record_id, state=None, proposal=None, decision="ACCEPT"):
    return {
        "id": record_id,
        "state": state
        or {"sim_or_real": "designed", "domain": "preference-curation-test"},
        "proposed_action": proposal
        or {"action": "bounded-noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": decision, "rationale": "fixture rationale"},
        "executed_action": {"action": "bounded-noop"},
        "future_outcome": {"success": decision != "REJECT"},
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {"tags": ["preference", "fixture"]},
    }


def pair(record_id="pair-1", chosen_state=None, rejected_state=None, proposal=None):
    shared_state = {"sim_or_real": "designed", "domain": "same-problem"}
    shared_proposal = proposal or {"action": "inspect", "decision_basis": "fixture"}
    return {
        "id": record_id,
        "chosen": trajectory(
            f"{record_id}-chosen",
            state=copy.deepcopy(chosen_state or shared_state),
            proposal=copy.deepcopy(shared_proposal),
            decision="MODIFY",
        ),
        "rejected": trajectory(
            f"{record_id}-rejected",
            state=copy.deepcopy(rejected_state or shared_state),
            proposal=copy.deepcopy(shared_proposal),
            decision="ACCEPT",
        ),
        "critique": "fixture preference",
        "reward_delta": {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
    }


def write_jsonl(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


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


class PreferencePurityNineteenRegression(unittest.TestCase):
    """Bind the nineteen known impure pairs to deterministic decisions.

    The committed corpus under tests/fixtures/preference-purity/ mirrors the
    real raw ffpc corpus line-for-line in layout and decision (10 files, 42
    records, 19 impure: 7 repaired + 12 excluded, 23 pure controls), as
    measured by a read-only scan of outputs/raw/2026-08-17/
    failure-as-fuel-preference-cascade. Raw stays immutable and unreferenced.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.curation_run = curate_preferences.curate_source(PURITY_FIXTURES)

    def decisions_by_location(self):
        return {
            (entry["source_path"], entry["source_line"]): entry
            for entry in self.curation_run.manifest
        }

    def test_summary_reproduces_the_real_corpus_figures(self):
        summary = self.curation_run.summary
        self.assertEqual(summary["json_records_seen"], 42)
        self.assertEqual(summary["preference_records"], 42)
        self.assertEqual(summary["skipped_non_preference_records"], 0)
        self.assertEqual(summary["impure_pairs"], 19)
        self.assertEqual(summary["retained_pairs"], 30)
        self.assertEqual(summary["excluded_pairs"], 12)
        self.assertEqual(
            summary["actions"], {"excluded": 12, "repaired": 7, "retained": 23}
        )
        self.assertEqual(
            summary["classifications"],
            {
                "already_same_context": 23,
                "attested_identity_annotation_only": 6,
                "attested_proposal_annotation_only": 1,
                "unsupported_context_divergence": 12,
            },
        )
        self.assertEqual(
            summary["reason_codes"],
            {
                "BRANCH_ONLY_IDENTITY_NOTE_REMOVED": 6,
                "BRANCH_ONLY_PROPOSAL_ANNOTATION_REMOVED": 1,
                "BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE": 3,
                "EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE": 6,
                "EXACT_PROPOSAL_COPIED_FROM_ATTESTED_REFERENCE": 1,
                "POLICY_MEMORY_CONTEXT_DIVERGES": 2,
                "PREFERENCE_CONTEXT_ALREADY_IDENTICAL": 23,
                "PROPOSED_ACTION_CONTEXT_DIVERGES": 7,
                "STATE_CONTEXT_DIVERGES": 6,
            },
        )
        self.assertEqual(summary["retained_context_purity_pct"], 100.0)

    def test_nineteen_impure_pairs_have_expected_decisions(self):
        by_location = self.decisions_by_location()
        impure = {
            location: entry
            for location, entry in by_location.items()
            if entry["action"] != curate_preferences.ACTION_RETAINED
        }
        self.assertEqual(sorted(impure), sorted(EXPECTED_IMPURE_DECISIONS))
        for location, (action, classification, reasons) in sorted(
            EXPECTED_IMPURE_DECISIONS.items()
        ):
            entry = by_location[location]
            self.assertEqual(entry["action"], action, location)
            self.assertEqual(entry["classification"], classification, location)
            self.assertEqual(tuple(entry["reason_codes"]), reasons, location)
        for entry in impure.values():
            self.assertTrue(entry["context_diff_paths"])

    def test_no_excluded_pair_needs_the_generic_fallback_reason(self):
        for entry in self.curation_run.manifest:
            self.assertNotIn("PREFERENCE_CONTEXT_DIVERGES", entry["reason_codes"])

    def test_documented_taxonomy_classes_appear_in_diff_paths(self):
        by_location = self.decisions_by_location()
        proposal_divergence = by_location[("batch-r05.jsonl", 2)]
        self.assertEqual(
            proposal_divergence["context_diff_paths"],
            [
                "proposed_action.content",
                "proposed_action.internal_reasoning_optimizer",
                "proposed_action.policy_confidence",
                "proposed_action.snn_readout.margin",
                "proposed_action.snn_readout.note",
                "proposed_action.snn_readout.runner_up",
                "proposed_action.snn_readout.winning_population",
                "proposed_action.source",
            ],
        )
        taxonomy_markers = {
            1: "state.environment.sensor_calibration_offset_c",  # state drift
            2: "proposed_action.content",  # action drift
            3: "state.timestamp_local",  # timestamp skew
            4: "proposed_action.tool",  # missing field
            5: "state.internal.scratchpad",  # extra field
            6: "state.observations[0].value",  # type coercion
        }
        for line, marker in taxonomy_markers.items():
            entry = by_location[("preferences.jsonl", line)]
            self.assertIn(marker, entry["context_diff_paths"], line)
            self.assertIsNone(entry["source_record_id"], line)
            paths = entry["context_diff_paths"]
            self.assertTrue(any(path.startswith("state") for path in paths), line)
            self.assertTrue(
                any(path.startswith("proposed_action") for path in paths), line
            )

    def test_decisions_are_deterministic_and_repairs_are_idempotent(self):
        second = curate_preferences.curate_source(PURITY_FIXTURES)
        self.assertEqual(self.curation_run, second)
        self.assertEqual(len(self.curation_run.records), 30)
        for record in self.curation_run.records:
            self.assertTrue(curate_preferences.context_is_pure(record))
            reapplied = curate_preferences.curate_preference_record(record)
            self.assertEqual(reapplied.action, curate_preferences.ACTION_RETAINED)
            self.assertEqual(reapplied.record, record)

    def test_curated_output_reaches_full_purity_in_strict_audit(self):
        source_audit_root = PURITY_FIXTURES.parent / "preference-purity-as-run"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # The fixture corpus itself must reproduce the historical audit
            # figures: 23/42 same-context (54.8%) and the 19/42 blocker.
            source_factory = root / "source-run" / "failure-as-fuel-preference-cascade"
            source_factory.mkdir(parents=True)
            for path in sorted(PURITY_FIXTURES.glob("*.jsonl")):
                (source_factory / path.name).write_bytes(path.read_bytes())
            source_audit = training_audit.audit_run(root / "source-run")
            self.assertEqual(source_audit["preferences"]["pairs"], 42)
            self.assertEqual(source_audit["preferences"]["same_context"], 23)
            self.assertEqual(
                source_audit["preferences"]["context_purity_pct"], 54.8
            )
            self.assertIn(
                "19/42 preference pairs change state or proposal",
                source_audit["blockers"],
            )
            self.assertIs(source_audit["training_ready"], False)

            # The curated output must audit at 100% purity with the
            # preference blocker gone.
            destination = root / "destination"
            destination.mkdir()
            output = destination / "preferences.jsonl"
            manifest = destination / "manifest.jsonl"
            curate_preferences.write_run(
                self.curation_run, PURITY_FIXTURES, output, manifest
            )
            audit_factory = root / "curated-run" / "failure-as-fuel-preference-cascade"
            audit_factory.mkdir(parents=True)
            (audit_factory / "preferences.jsonl").write_bytes(output.read_bytes())
            curated_audit = training_audit.audit_run(root / "curated-run")
            self.assertEqual(curated_audit["preferences"]["pairs"], 30)
            self.assertEqual(curated_audit["preferences"]["same_context"], 30)
            self.assertEqual(
                curated_audit["preferences"]["context_purity_pct"], 100.0
            )
            for blocker in curated_audit["blockers"]:
                self.assertNotIn("preference pairs change state or proposal", blocker)
            # Audited alone, the curated preference lane clears every strict
            # gate. This is a per-lane statement: the full corpus stays
            # blocked until the remaining sf-c5l lanes land.
            self.assertEqual(curated_audit["blockers"], [])
            self.assertIs(curated_audit["training_ready"], True)

            emitted = [
                json.loads(line) for line in output.read_text().splitlines()
            ]
            self.assertEqual(len(emitted), 30)
            self.assertTrue(
                all(curate_preferences.context_is_pure(item) for item in emitted)
            )
        self.assertFalse(source_audit_root.exists())

    def test_fixture_sources_stay_byte_identical_and_writer_refuses_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td)
            run = curate_preferences.curate_source(PURITY_FIXTURES)
            curate_preferences.write_run(
                run,
                PURITY_FIXTURES,
                destination / "preferences.jsonl",
                destination / "manifest.jsonl",
            )
            with self.assertRaisesRegex(
                curate_preferences.PreferenceCurationError, "refusing overwrite"
            ):
                curate_preferences.write_run(
                    run,
                    PURITY_FIXTURES,
                    destination / "preferences.jsonl",
                    destination / "manifest-2.jsonl",
                )
            with self.assertRaisesRegex(
                curate_preferences.PreferenceCurationError, "inside source"
            ):
                curate_preferences.write_run(
                    run,
                    PURITY_FIXTURES,
                    PURITY_FIXTURES / "curated.jsonl",
                    destination / "manifest-3.jsonl",
                )
            with self.assertRaisesRegex(
                curate_preferences.PreferenceCurationError,
                "output and manifest destinations must differ",
            ):
                curate_preferences.write_run(
                    run,
                    PURITY_FIXTURES,
                    destination / "aliased.jsonl",
                    destination / "aliased.jsonl",
                )
        hashes_after = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(PURITY_FIXTURES.glob("*.jsonl"))
        }
        self.assertEqual(hashes_after, GOLDEN_FIXTURE_SHA256)


RAW_FFPC = (
    REPO / "outputs" / "raw" / "2026-08-17" / "failure-as-fuel-preference-cascade"
)


@unittest.skipUnless(
    RAW_FFPC.is_dir(),
    "raw ffpc corpus not present in this checkout (gitignored); "
    "fidelity is re-derived only where the immutable raw tree exists",
)
class PreferencePurityRawCorpusFidelity(unittest.TestCase):
    """Independently verify the fixture corpus corresponds to the raw corpus.

    The committed fixture mirrors the real raw ffpc corpus by construction,
    but the committed evidence (golden hashes, expected decisions) is authored
    alongside the fixture. Where the gitignored raw tree is present, this
    read-only check re-derives the correspondence from first principles: the
    raw scan must reproduce the bead figures, and the fixture must reproduce
    the raw corpus's summary and per-line decision map exactly.
    """

    def test_fixture_decision_map_matches_a_fresh_raw_corpus_scan(self):
        raw_run = curate_preferences.curate_source(RAW_FFPC)
        fixture_run = curate_preferences.curate_source(PURITY_FIXTURES)

        self.assertEqual(raw_run.summary["preference_records"], 42)
        self.assertEqual(raw_run.summary["impure_pairs"], 19)
        comparable_keys = (
            "json_records_seen",
            "preference_records",
            "skipped_non_preference_records",
            "impure_pairs",
            "retained_pairs",
            "excluded_pairs",
            "actions",
            "classifications",
            "reason_codes",
            "retained_context_purity_pct",
        )
        for key in comparable_keys:
            self.assertEqual(
                fixture_run.summary[key], raw_run.summary[key], key
            )

        def decision_map(run):
            return {
                (entry["source_path"], entry["source_line"]): (
                    entry["action"],
                    entry["classification"],
                    tuple(entry["reason_codes"]),
                )
                for entry in run.manifest
            }

        self.assertEqual(decision_map(fixture_run), decision_map(raw_run))


if __name__ == "__main__":
    unittest.main()
