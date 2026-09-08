#!/usr/bin/env python3
"""The export: integrity refuses, ineligibility never blocks, splits hold, bytes are stable."""

import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (  # noqa: E402
    FIXTURE_CATALOG, cli, envelope, generate, oc, refusal, smoke_run, verify, views, vocabulary as cv,
)
from code_repair import export, lineage, replay  # noqa: E402


def export_of(run_dir, root, replay_dir=None, cap=export.DEFAULT_LINEAGE_CAP):
    out = Path(root) / "export"
    manifest = export.run(export.ExportRequest(run_dir, out, replay_dir, cap))
    return manifest, out


def restamp(record):
    record["result"]["evidence_sha256"] = verify.result_hash(record["result"]["phases"])
    record["provenance"]["record_sha256"] = envelope.record_digest(record)
    return record


def run_copy(root, records=None):
    """A private copy of the smoke run, optionally with its records replaced."""

    _summary, loaded, run_dir = smoke_run()
    copied = Path(root) / "run"
    shutil.copytree(run_dir, copied)
    if records is not None:
        (copied / generate.CANDIDATES_FILENAME).unlink()
        oc.write_jsonl(copied / generate.CANDIDATES_FILENAME, records)
    return copied, [copy.deepcopy(r) for r in loaded]


class Artifacts(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-export-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_the_tree_holds_evidence_split_rows_consumer_rows_freeze_and_manifest(self):
        _summary, records, run_dir = smoke_run()
        manifest, out = export_of(run_dir, self.root)
        positives = [r for r in records if views.is_positive(r)]
        self.assertEqual(manifest["tables"]["positives"], len(positives))
        self.assertEqual(manifest["tables"]["records"], len(records))
        self.assertEqual(manifest["tables"]["dispositions"]["exported"], len(positives))
        evidence = [r for _n, r in oc.read_jsonl(out / export.EVIDENCE_PATH)]
        self.assertEqual(evidence, records)
        rows = {s: [r for _n, r in oc.read_jsonl(out / f"sft/{s}.jsonl")] for s in lineage.SPLITS}
        self.assertEqual(sum(len(v) for v in rows.values()), len(positives))
        self.assertTrue(all(set(r) == {"prompt", "completion"} for v in rows.values() for r in v))
        agoge = [r for _n, r in oc.read_jsonl(out / export.AGOGE_PATH)]
        self.assertEqual(len(agoge), len(positives))
        self.assertEqual(set(agoge[0]), {"canonical_id", "lineage_id", "group_id", "split", "text"})
        freeze = json.loads((out / export.FREEZE_PATH).read_text())
        self.assertEqual(freeze["canonical_ids"], [r["canonical_id"] for r in agoge if r["split"] == "held_out"])
        for relative, digest in manifest["files"].items():
            self.assertEqual(hashlib.sha256((out / relative).read_bytes()).hexdigest(), digest)
        self.assertEqual(manifest["pipeline_status"], "complete")
        self.assertEqual(manifest["admission"]["training_export"], "blocked")
        self.assertIn(cv.BLOCKER_REPLAY_NOT_RUN, manifest["admission"]["blockers"])
        self.assertEqual(manifest["replay"], "not run")

    def test_two_exports_of_one_run_are_byte_identical_and_a_replay_lifts_its_blocker(self):
        _summary, _records, run_dir = smoke_run()
        replay_dir = self.root / "replay"
        replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, replay_dir, 5.0))
        first, out_a = export_of(run_dir, self.root / "a", replay_dir)
        second, out_b = export_of(run_dir, self.root / "b", replay_dir)
        self.assertEqual(first["files"], second["files"])
        for relative in first["files"]:
            self.assertEqual((out_a / relative).read_bytes(), (out_b / relative).read_bytes())
        self.assertEqual((out_a / export.MANIFEST_FILENAME).read_bytes(), (out_b / export.MANIFEST_FILENAME).read_bytes())
        self.assertEqual(first["replay"], "passed")
        self.assertNotIn(cv.BLOCKER_REPLAY_NOT_RUN, first["admission"]["blockers"])

    def test_request_refusals(self):
        _summary, _records, run_dir = smoke_run()
        with refusal(self, cv.FINDING_RUN_FILE_MISSING):
            export.run(export.ExportRequest(self.root / "nowhere", self.root / "out"))
        (self.root / "taken").mkdir()
        with refusal(self, cv.FINDING_DESTINATION_EXISTS):
            export.run(export.ExportRequest(run_dir, self.root / "taken"))
        with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW):
            export.run(export.ExportRequest(run_dir, self.root / "outputs" / "raw" / "x"))
        with refusal(self, cv.FINDING_CAP_OUT_OF_DOMAIN):
            export.run(export.ExportRequest(run_dir, self.root / "out", None, 0))
        with refusal(self, cv.FINDING_REPLAY_FILE_MISSING):
            export.run(export.ExportRequest(run_dir, self.root / "out", self.root / "no-replay"))


class Integrity(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-export-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def tampered_run(self, tamper, restamped=True, name="tampered"):
        run_dir, records = run_copy(self.root / name)
        positive = next(i for i, r in enumerate(records) if views.is_positive(r))
        tamper(records[positive])
        if restamped:
            restamp(records[positive])
        (run_dir / generate.CANDIDATES_FILENAME).unlink()
        oc.write_jsonl(run_dir / generate.CANDIDATES_FILENAME, records)
        return run_dir

    def test_an_edited_row_or_verdict_refuses_the_whole_export(self):
        cases = (
            ("digest", lambda r: r["result"]["phases"]["mutant"]["public"][0].update(status="pass"), False),
            ("verdict", lambda r: r["result"].update(outcome=cv.OUTCOME_REJECTED), True),
            ("label", lambda r: r["scenario"].update(outcome="accepted"), True),
        )
        for name, tamper, restamped in cases:
            with self.subTest(name=name), refusal(self, cv.FINDING_EXPORT_INTEGRITY, "integrity"):
                run_dir = self.tampered_run(tamper, restamped, name)
                export.run(export.ExportRequest(run_dir, self.root / f"out-{name}"))

    def test_a_failed_or_missing_replay_of_a_positive_refuses_but_ineligible_records_never_do(self):
        _summary, _records, run_dir = smoke_run()
        replay_dir = self.root / "replay"
        replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, replay_dir, 5.0))
        report_path = replay_dir / replay.REPLAY_FILENAME
        report = json.loads(report_path.read_text())
        entry = next(e for e in report["records"] if e["status"] == "replayed")
        entry["code"] = cv.REPLAY_ROWS_MISMATCH
        report_path.write_text(json.dumps(report))
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, cv.REPLAY_ROWS_MISMATCH):
            export.run(export.ExportRequest(run_dir, self.root / "out", replay_dir))
        manifest, _out = export_of(run_dir, self.root / "plain")
        self.assertGreater(manifest["tables"]["outcomes"]["rejected"], 0)
        self.assertGreater(manifest["tables"]["oracle_statuses"]["provisional"], 0)
        self.assertEqual(manifest["tables"]["dispositions"]["exported"], manifest["tables"]["positives"])

    def test_a_lineage_in_two_splits_or_a_moved_split_refuses(self):
        def move(record):
            block = record["provenance"]["split_lineage"]
            block["split"] = "validation" if block["split"] != "validation" else "train"

        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, cv.EXPORT_SPLIT_REDERIVATION_MISMATCH):
            export.run(export.ExportRequest(self.tampered_run(move), self.root / "out-moved"))
        run_dir, records = run_copy(self.root / "cross")
        (run_dir / generate.CANDIDATES_FILENAME).unlink()
        positives = [r for r in records if views.is_positive(r)]
        for record in records:
            record["provenance"]["split_lineage"]["policy_sha256"] = None
        move(positives[0])
        restamp(positives[0])
        run_meta = json.loads((run_dir / generate.RUN_FILENAME).read_text())
        (run_dir / generate.RUN_FILENAME).write_text(json.dumps({**run_meta, "split_policy": None}))
        oc.write_jsonl(run_dir / generate.CANDIDATES_FILENAME, [restamp(r) for r in records])
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY):
            export.run(export.ExportRequest(run_dir, self.root / "out-cross"))


class DedupAndAdmission(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-export-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_exact_duplicates_and_the_lineage_cap_are_dispositions_not_refusals(self):
        run_dir, records = run_copy(self.root)
        positives = [r for r in records if views.is_positive(r)]
        twin = copy.deepcopy(positives[0])
        twin["id"] = twin["id"] + "-twin"
        restamp(twin)
        (run_dir / generate.CANDIDATES_FILENAME).unlink()
        oc.write_jsonl(run_dir / generate.CANDIDATES_FILENAME, records + [twin])
        manifest, _out = export_of(run_dir, self.root / "dup")
        self.assertEqual(manifest["tables"]["dispositions"][cv.EXPORT_DUPLICATE_EXACT], 1)
        manifest, _out = export_of(run_dir, self.root / "cap", cap=1)
        self.assertLessEqual(max(manifest["tables"]["per_lineage_exported"].values()), 1)
        self.assertIn(cv.EXPORT_LINEAGE_CAP_APPLIED, manifest["tables"]["dispositions"])

    def test_admission_blockers_never_include_an_evaluation_limitation(self):
        cleared = export.Gates(True, True, True, True)
        self.assertEqual(export.admission_blockers(cleared, replay_passed=True, exported_rows=3), [])
        self.assertEqual(
            export.admission_blockers(cleared, replay_passed=True, exported_rows=0),
            [cv.BLOCKER_NO_VALIDATED_ACCEPTED_ROWS],
        )
        everything = export.admission_blockers(export.Gates(), replay_passed=False, exported_rows=0)
        self.assertEqual(set(everything), cv.BLOCKER_CODE_SET)
        self.assertFalse(set(everything) & cv.LIMITATION_CODE_SET)
        _summary, _records, run_dir = smoke_run()
        manifest, _out = export_of(run_dir, self.root / "lim")
        self.assertEqual(manifest["evaluation_limitations"], list(cv.LIMITATION_CODES))
        self.assertFalse(set(manifest["admission"]["blockers"]) & cv.LIMITATION_CODE_SET)
        self.assertEqual(manifest["training_run_prerequisites"], list(cv.PREREQUISITE_CODES))

    def test_the_cli_exports_with_exit_zero(self):
        _summary, _records, run_dir = smoke_run()
        code = cli.run(["export", "--run", str(run_dir), "--out", str(self.root / "cli-out"), "--json"])
        self.assertEqual(code, 0)
        self.assertTrue((self.root / "cli-out" / export.MANIFEST_FILENAME).is_file())


if __name__ == "__main__":
    unittest.main()
