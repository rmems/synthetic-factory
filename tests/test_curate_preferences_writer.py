#!/usr/bin/env python3
"""Source-scan and writer tests for same-context preference curation."""

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import curate_preferences  # noqa: E402
import training_audit  # noqa: E402


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

    def test_writer_refuses_every_destination_under_outputs_raw(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw_factory = root / "outputs" / "raw" / "2026-08-17" / "ffpc"
            raw_factory.mkdir(parents=True)
            source_path = raw_factory / "preferences.jsonl"
            write_jsonl(source_path, [pair("raw-guard")])
            outside = root / "cleaned"
            outside.mkdir()

            # A single-file source has no directory for the "inside source"
            # check to bite on, and a directory source does not contain its own
            # siblings; only the raw-tree guard stops either write.
            for source, output, manifest in (
                (source_path, raw_factory / "curated.jsonl", outside / "m1.jsonl"),
                (source_path, outside / "o1.jsonl", raw_factory / "manifest.jsonl"),
                (
                    raw_factory,
                    raw_factory.parent / "curated.jsonl",
                    outside / "m2.jsonl",
                ),
            ):
                with self.subTest(output=str(output), manifest=str(manifest)):
                    run = curate_preferences.curate_source(source)
                    with self.assertRaisesRegex(
                        curate_preferences.PreferenceCurationError,
                        "immutable raw evidence",
                    ):
                        curate_preferences.write_run(run, source, output, manifest)

            self.assertEqual(
                sorted(path.name for path in raw_factory.rglob("*")),
                ["preferences.jsonl"],
            )
            self.assertEqual(list(raw_factory.parent.iterdir()), [raw_factory])
            self.assertEqual(list(outside.iterdir()), [])

            run = curate_preferences.curate_source(source_path)
            curate_preferences.write_run(
                run, source_path, outside / "ok.jsonl", outside / "ok-manifest.jsonl"
            )
            self.assertEqual(
                sorted(path.name for path in outside.iterdir()),
                ["ok-manifest.jsonl", "ok.jsonl"],
            )

    def test_writer_refuses_symlinked_outputs_raw_destination(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.jsonl"
            write_jsonl(source, [pair("symlinked-raw-guard")])
            outputs = root / "outputs"
            external_raw = root / "mounted-raw"
            outside = root / "cleaned"
            outputs.mkdir()
            external_raw.mkdir()
            outside.mkdir()
            (outputs / "raw").symlink_to(external_raw, target_is_directory=True)

            run = curate_preferences.curate_source(source)
            destination = outputs / "raw" / "curated.jsonl"
            with self.assertRaisesRegex(
                curate_preferences.PreferenceCurationError,
                "immutable raw evidence",
            ):
                curate_preferences.write_run(
                    run, source, destination, outside / "manifest.jsonl"
                )

            self.assertFalse((external_raw / "curated.jsonl").exists())
            self.assertEqual(list(outside.iterdir()), [])

    def test_writer_refuses_resolved_target_of_symlinked_outputs_raw(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.jsonl"
            write_jsonl(source, [pair("resolved-raw-alias-guard")])
            outputs = root / "outputs"
            external_raw = root / "mounted-raw"
            outside = root / "cleaned"
            outputs.mkdir()
            external_raw.mkdir()
            outside.mkdir()
            raw_root = outputs / "raw"
            raw_root.symlink_to(external_raw, target_is_directory=True)

            run = curate_preferences.curate_source(source)
            destination = external_raw / "curated.jsonl"
            with mock.patch.object(curate_preferences, "RAW_OUTPUT_ROOT", raw_root):
                with self.assertRaisesRegex(
                    curate_preferences.PreferenceCurationError,
                    "immutable raw evidence",
                ):
                    curate_preferences.write_run(
                        run, source, destination, outside / "manifest.jsonl"
                    )

            self.assertFalse(destination.exists())
            self.assertFalse((raw_root / destination.name).exists())
            self.assertEqual(list(outside.iterdir()), [])

    def test_writer_refuses_alternate_alias_of_symlinked_outputs_raw(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.jsonl"
            write_jsonl(source, [pair("second-raw-alias-guard")])
            outputs = root / "outputs"
            external_raw = root / "mounted-raw"
            alternate_alias = root / "raw-alias"
            outside = root / "cleaned"
            outputs.mkdir()
            external_raw.mkdir()
            outside.mkdir()
            raw_root = outputs / "raw"
            raw_root.symlink_to(external_raw, target_is_directory=True)
            alternate_alias.symlink_to(external_raw, target_is_directory=True)

            run = curate_preferences.curate_source(source)
            output = outside / "curated.jsonl"
            manifest = alternate_alias / "manifest.jsonl"
            with mock.patch.object(curate_preferences, "RAW_OUTPUT_ROOT", raw_root):
                with self.assertRaisesRegex(
                    curate_preferences.PreferenceCurationError,
                    "immutable raw evidence",
                ):
                    curate_preferences.write_run(run, source, output, manifest)

            self.assertFalse(output.exists())
            self.assertFalse(manifest.exists())
            self.assertFalse((raw_root / manifest.name).exists())

    def test_non_encodable_record_is_excluded_without_aborting_the_scan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            destination.mkdir()
            # ``json.loads`` accepts the non-standard ``NaN`` literal, so a raw
            # line really can carry a float that cannot be re-encoded.
            source_path = source / "preferences.jsonl"
            source_path.write_text(
                json.dumps(pair("good"))
                + "\n"
                + '{"id": NaN, "chosen": {"state": {"a": NaN}, "proposed_action": {}},'
                + ' "rejected": {"state": {"a": 1}, "proposed_action": {}}}\n'
            )

            run = curate_preferences.curate_source(source)

            self.assertEqual(run.summary["preference_records"], 2)
            self.assertEqual(run.summary["retained_pairs"], 1)
            self.assertEqual(run.summary["excluded_pairs"], 1)
            self.assertEqual(
                run.summary["reason_codes"]["PREFERENCE_RECORD_NOT_JSON_SERIALIZABLE"],
                1,
            )
            self.assertEqual(run.summary["retained_context_purity_pct"], 100.0)

            bad = run.manifest[1]
            self.assertEqual(bad["action"], curate_preferences.ACTION_EXCLUDED)
            self.assertEqual(bad["source_path"], "preferences.jsonl")
            self.assertEqual(bad["source_line"], 2)
            self.assertEqual(
                bad["source_sha256"],
                hashlib.sha256(source_path.read_bytes().splitlines()[1]).hexdigest(),
            )
            # The unencodable id is dropped; path, line, and hash still point
            # at the preserved source line.
            self.assertIsNone(bad["source_record_id"])
            self.assertIsNone(bad["output_sha256"])

            output = destination / "preferences.jsonl"
            curate_preferences.write_run(
                run, source, output, destination / "manifest.jsonl"
            )
            emitted = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual([item["id"] for item in emitted], ["good"])

    def test_lone_surrogate_record_is_excluded_without_aborting_the_scan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.jsonl"
            destination = root / "destination"
            destination.mkdir()
            source.write_bytes(
                json.dumps(pair("good")).encode("utf-8")
                + b"\n"
                + b'{"id":"lone-surrogate","chosen":{"state":{"value":"\\ud800"},'
                + b'"proposed_action":{}},"rejected":{"state":{"value":"\\ud800"},'
                + b'"proposed_action":{}}}\n'
            )

            run = curate_preferences.curate_source(source)

            self.assertEqual(run.summary["preference_records"], 2)
            self.assertEqual(run.summary["retained_pairs"], 1)
            self.assertEqual(run.summary["excluded_pairs"], 1)
            self.assertEqual(
                run.summary["reason_codes"][
                    "PREFERENCE_RECORD_NOT_JSON_SERIALIZABLE"
                ],
                1,
            )
            bad = run.manifest[1]
            self.assertEqual(bad["action"], curate_preferences.ACTION_EXCLUDED)
            self.assertEqual(bad["source_record_id"], "lone-surrogate")
            self.assertEqual(bad["source_line"], 2)
            self.assertIsNone(bad["output_sha256"])

            output = destination / "preferences.jsonl"
            curate_preferences.write_run(
                run, source, output, destination / "manifest.jsonl"
            )
            emitted = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual([item["id"] for item in emitted], ["good"])

    def test_purity_percent_is_zero_when_nothing_is_retained(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "preferences.jsonl"
            divergent = pair("all-excluded", rejected_state={"sim_or_real": "designed"})
            write_jsonl(source, [divergent])

            run = curate_preferences.curate_source(source)

            self.assertEqual(run.summary["retained_pairs"], 0)
            self.assertEqual(run.summary["retained_context_purity_pct"], 0.0)

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
