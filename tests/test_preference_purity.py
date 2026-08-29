#!/usr/bin/env python3
"""The nineteen-impure-pair purity regression and its raw-corpus fidelity.

Pins the committed preference-purity fixture corpus by golden digest, asserts
the per-pair curation decisions line-for-line, and independently re-derives
the fixtures from the immutable raw tree where that tree is present.
"""

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
