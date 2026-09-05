#!/usr/bin/env python3
"""Tests for the distillation validator and the committed fixture run."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import energy_preferences as ep  # noqa: E402
import fault_recovery as fr  # noqa: E402
import moe_router as mr  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402
import router_baseline as rb  # noqa: E402
import validate_distill as vd  # noqa: E402

FIXTURE = REPO / "tests" / "fixtures" / "distillation-run"


class Routing(unittest.TestCase):
    def test_every_family_has_a_registered_checker(self):
        self.assertEqual(set(vd.FAMILY_CHECKS), set(oc.FAMILIES))

    def test_each_family_record_reaches_its_own_checker(self):
        cases = [
            (fr.build_records(3, 1)[0], "intervention", "kind"),
            (mr.build_records(3, 1)[0], "result", "routing"),
        ]
        for record, block, key in cases:
            with self.subTest(family=record["family"]):
                self.assertEqual(vd.check_record(record, "x"), [])
                broken = json.loads(json.dumps(record))
                broken[block].pop(key)
                self.assertTrue(vd.check_record(broken, "x"))

    def test_a_non_object_record_is_reported(self):
        self.assertTrue(vd.check_record(["not", "an", "object"], "x"))

    def test_an_unknown_family_is_reported_once(self):
        record = fr.build_records(3, 1)[0]
        record["family"] = "made-up-family"
        errors = vd.check_record(record, "x")
        self.assertTrue(any("family must be one of" in error for error in errors))


class ValidatePath(unittest.TestCase):
    def write_run(self, tmp):
        root = Path(tmp) / "run"
        oc.write_jsonl(root / "fault-recovery" / "batch.jsonl", fr.build_records(3, 6))
        oc.write_jsonl(root / "moe-router" / "batch.jsonl", mr.build_records(3, 4))
        return root

    def test_a_clean_run_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = vd.validate_path(self.write_run(tmp))
            self.assertEqual(report["invalid"], 0)
            self.assertEqual(report["records"], 10)
            self.assertFalse(report["blocked"])

    def test_reference_only_records_are_valid_but_not_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = vd.validate_path(self.write_run(tmp))
            self.assertEqual(report["valid"], 10)
            self.assertEqual(report["curation_eligible"], 6)
            self.assertIn(
                "ORACLE_NOT_AUTHORITATIVE:'reference_only'",
                report["curation_ineligible_reasons"],
            )

    def test_strict_mode_blocks_on_ineligible_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.write_run(tmp)
            self.assertFalse(vd.validate_path(root)["blocked"])
            self.assertTrue(vd.validate_path(root, strict=True)["blocked"])

    def test_a_parse_failure_is_reported_not_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.write_run(tmp)
            with (root / "fault-recovery" / "batch.jsonl").open(
                "a", encoding="utf-8"
            ) as handle:
                handle.write("{ not json\n")
            report = vd.validate_path(root)
            self.assertTrue(report["blocked"])
            self.assertTrue(
                any("JSON parse failure" in f["error"] for f in report["findings"])
            )

    def test_duplicate_ids_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            records = fr.build_records(3, 2)
            oc.write_jsonl(root / "a.jsonl", records)
            oc.write_jsonl(root / "b.jsonl", records)
            report = vd.validate_path(root)
            self.assertTrue(
                any("duplicate record id" in f["error"] for f in report["findings"])
            )

    def test_a_hand_edited_record_fails_the_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            record = fr.build_records(3, 1)[0]
            record["result"]["outcome"] = "continue"
            oc.write_jsonl(root / "a.jsonl", [record])
            report = vd.validate_path(root)
            self.assertTrue(
                any("record_sha256 mismatch" in f["error"] for f in report["findings"])
            )

    def test_an_empty_directory_is_a_failure_not_a_clean_run(self):
        # A typo in the path or a generation step that produced nothing must
        # not report "0 records, 0 invalid" and exit zero.
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty"
            empty.mkdir()
            report = vd.validate_path(empty)
            self.assertTrue(report["blocked"])
            self.assertTrue(
                any("no .jsonl files" in f["error"] for f in report["findings"])
            )

    def test_a_directory_of_empty_files_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            root.mkdir()
            (root / "batch.jsonl").write_text("")
            report = vd.validate_path(root)
            self.assertTrue(report["blocked"])
            self.assertTrue(
                any("no records found" in f["error"] for f in report["findings"])
            )

    def test_a_non_finite_constant_does_not_abort_the_whole_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            root.mkdir()
            good = fr.build_records(3, 1)[0]
            (root / "batch.jsonl").write_text(
                '{"id": "bad", "value": NaN}\n' + oc.canonical_json(good) + "\n"
            )
            report = vd.validate_path(root)
            self.assertEqual(report["records"], 2)
            self.assertEqual(report["valid"], 1)
            self.assertTrue(
                any("JSON parse failure" in f["error"] for f in report["findings"])
            )

    def test_a_missing_path_raises(self):
        with self.assertRaises(FileNotFoundError):
            vd.validate_path(Path("/nonexistent/distillation/run"))

    def test_a_single_file_target_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "one.jsonl"
            oc.write_jsonl(path, fr.build_records(3, 2))
            report = vd.validate_path(path)
            self.assertEqual(report["files"], 1)
            self.assertEqual(report["records"], 2)


class Stamping(unittest.TestCase):
    def test_stamp_output_writes_validator_owned_verdicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            oc.write_jsonl(root / "a.jsonl", fr.build_records(3, 2))
            out = Path(tmp) / "stamped.jsonl"
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = vd.main([str(root), "--stamp-output", str(out)])
            self.assertEqual(exit_code, 0)
            stamped = [obj for _, obj in oc.read_jsonl(out)]
            self.assertEqual(len(stamped), 2)
            for record in stamped:
                self.assertEqual(record["validation"]["status"], "passed")
                self.assertEqual(
                    record["validation"]["validator"]["name"], vd.VALIDATOR_NAME
                )
                self.assertEqual(oc.check_envelope(record, "x"), [])
                self.assertEqual(oc.check_digest(record, "x"), [])

    def test_findings_are_stamped_as_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            record = fr.build_records(3, 1)[0]
            record["result"]["reason_codes"] = []
            record["provenance"]["record_sha256"] = oc.record_digest(record)
            oc.write_jsonl(root / "a.jsonl", [record])
            out = Path(tmp) / "stamped.jsonl"
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.redirect_stderr(io.StringIO()):
                    exit_code = vd.main([str(root), "--stamp-output", str(out)])
            self.assertEqual(exit_code, 1)
            stamped = [obj for _, obj in oc.read_jsonl(out)][0]
            self.assertEqual(stamped["validation"]["status"], "failed")
            self.assertTrue(stamped["validation"]["findings"])


class Cli(unittest.TestCase):
    def test_missing_path_exits_two(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(vd.main(["/nonexistent/distill"]), 2)

    def test_json_flag_includes_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            oc.write_jsonl(root / "a.jsonl", fr.build_records(3, 1))
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                vd.main([str(root), "--json"])
            report = json.loads(buffer.getvalue())
            self.assertIn("findings", report)

    def test_default_summary_omits_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            oc.write_jsonl(root / "a.jsonl", fr.build_records(3, 1))
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                vd.main([str(root)])
            report = json.loads(buffer.getvalue())
            self.assertNotIn("findings", report)


class CommittedFixtureRun(unittest.TestCase):
    """The fixture is a real run, so it must survive the real validator."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (FIXTURE / "MANIFEST.json").read_text(encoding="utf-8")
        )
        cls.report = vd.validate_path(FIXTURE)

    def test_the_fixture_validates_cleanly(self):
        self.assertEqual(self.report["invalid"], 0, self.report["findings"][:3])
        self.assertGreater(self.report["records"], 0)
        self.assertFalse(self.report["blocked"])

    def test_all_three_families_are_present(self):
        self.assertEqual(set(self.report["families"]), set(oc.FAMILIES))

    def test_every_fault_outcome_appears(self):
        self.assertEqual(set(self.report["fault_outcomes"]), set(fr.OUTCOMES))

    def test_manifest_totals_match_a_fresh_validation(self):
        for key in ("records", "valid", "invalid", "curation_eligible"):
            self.assertEqual(self.manifest["validation"][key], self.report[key])

    def test_manifest_file_digests_match_the_committed_files(self):
        import hashlib

        for relative, entry in self.manifest["files"].items():
            path = FIXTURE / relative
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, entry["sha256"], relative)
            self.assertEqual(len(oc.read_jsonl(path)), entry["records"])

    def test_manifest_does_not_claim_training_readiness(self):
        self.assertFalse(self.manifest["training_ready"])
        self.assertTrue(self.manifest["training_ready_note"])

    def test_manifest_names_every_unavailable_oracle(self):
        oracles = self.manifest["oracles"]
        self.assertTrue(oracles[mr.FAMILY]["unavailable"])
        self.assertFalse(oracles[mr.FAMILY]["is_llm_teacher"])
        self.assertEqual(
            oracles[mr.FAMILY]["authority"], oc.AUTHORITY_REFERENCE_ONLY
        )
        self.assertTrue(oracles[fr.FAMILY]["unavailable"])

    def test_manifest_unavailability_comes_from_a_probe_not_a_constant(self):
        # The manifest is an audit of the producing environment, so a rebuild
        # on a host where transformers imports must say so rather than repeat
        # this machine's answer.
        probe = self.manifest["oracles"][mr.FAMILY]["oracle_probe"]
        recorded = self.manifest["oracles"][mr.FAMILY]["unavailable"]
        expected = [
            f"{entry['name']} ({entry['detail']})"
            for entry in probe["oracles"]
            if not entry["available"]
        ]
        self.assertEqual(recorded, expected)
        for entry in probe["oracles"]:
            self.assertTrue(entry["detail"])

    def test_energy_records_do_not_claim_joules_they_did_not_measure(self):
        energy = self.manifest["oracles"][ep.FAMILY]
        if not energy["cost_is_energy"]:
            self.assertEqual(energy["cost_quantity"], "cpu_time_s")
            self.assertIn("intel_rapl_powercap", energy["unavailable"])
        path = FIXTURE / "energy-preferences" / "batch-r01.jsonl"
        for _, record in oc.read_jsonl(path):
            self.assertEqual(
                record["result"]["cost_is_energy"], energy["cost_is_energy"]
            )
            self.assertEqual(oc.check_no_theoretical_energy_claim(record, "x"), [])

    def test_the_energy_preference_respects_quality_and_safety(self):
        path = FIXTURE / "energy-preferences" / "batch-r01.jsonl"
        for _, record in oc.read_jsonl(path):
            preference = record["result"]["preference"]
            by_id = {c["id"]: c for c in record["result"]["candidates"]}
            preferred = by_id[preference["preferred"]]
            self.assertTrue(preferred["safety_ok"])
            self.assertGreaterEqual(
                preferred["task_quality"],
                record["scenario"]["constraints"]["quality_floor"],
            )
            self.assertTrue(preference["cheaper_but_constraint_violating"])

    def test_the_baseline_report_is_reproducible_from_the_fixture(self):
        path = FIXTURE / "moe-router" / "batch-r01.jsonl"
        records = [obj for _, obj in oc.read_jsonl(path)]
        samples = rb.dataset_from_records(records)
        report = rb.evaluate_baselines(samples)
        recorded = self.manifest["baseline"]
        self.assertEqual(report["verdict"], recorded["verdict"])
        self.assertEqual(report["baselines"], recorded["baselines"])
        self.assertEqual(
            rb.escalation_gate(report)["escalate_to_snn"],
            recorded["escalation"]["escalate_to_snn"],
        )

    def test_the_baseline_ran_before_any_snn_claim(self):
        recorded = self.manifest["baseline"]
        self.assertIn("majority_class", recorded["baselines"])
        self.assertIn("logistic_regression", recorded["baselines"])
        self.assertIn("mlp", recorded["baselines"])
        self.assertIn("escalation", recorded)


class FixtureBuilder(unittest.TestCase):
    """The committed fixture must be rebuildable by the committed script."""

    def test_building_into_a_temp_dir_produces_a_valid_run(self):
        sys.path.insert(0, str(REPO / "scripts"))
        import build_distillation_fixture as builder

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            manifest = builder.build(out)
            self.assertEqual(manifest["validation"]["invalid"], 0)
            self.assertFalse(manifest["training_ready"])
            report = vd.validate_path(out)
            self.assertEqual(report["invalid"], 0)
            self.assertEqual(set(report["families"]), set(oc.FAMILIES))

    def test_it_refuses_to_clobber_an_existing_run_without_force(self):
        sys.path.insert(0, str(REPO / "scripts"))
        import build_distillation_fixture as builder

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            out.mkdir()
            with self.assertRaises(SystemExit):
                builder.build(out)


if __name__ == "__main__":
    unittest.main()
