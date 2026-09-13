#!/usr/bin/env python3
"""The export: integrity refuses, ineligibility never blocks, splits hold, bytes are stable."""

import copy
import hashlib
import json
import shutil
import contextlib
import io
import itertools
from collections import Counter
from unittest import mock
import tempfile
import unittest
from pathlib import Path

from tests.code_repair_test_support import (
    FIXTURE_CATALOG, cli, envelope, generate, oc, refusal, smoke_run, verify, views,
    vocabulary as cv,
)
from code_repair import export, lineage, replay
from code_repair._contract import ExactJSONFloat, exact_fraction, load_strict_json
from scripts import agoge_consumer_probe as probe


def request(run_dir, out_dir, replay_dir=None, cap=export.DEFAULT_LINEAGE_CAP):
    return export.ExportRequest(
        run_dir, out_dir, replay_dir, cap, catalog_dir=FIXTURE_CATALOG
    )


def stamp_replay(run_dir, replay_dir):
    path = replay_dir / replay.REPLAY_FILENAME
    report = json.loads(path.read_text())
    path.write_text(json.dumps(report))
    return report


def stamp_summary(run_dir, records):
    path = run_dir / generate.RUN_FILENAME
    meta = json.loads(path.read_text())
    meta.update(records=len(records))
    for key, field in (("outcomes", "outcome"), ("oracle_statuses", "oracle_status")):
        meta[key] = dict(Counter(r["result"][field] for r in records))
    path.write_text(json.dumps(meta))


def export_of(run_dir, root, replay_dir=None, cap=export.DEFAULT_LINEAGE_CAP):
    out = Path(root) / "export"
    manifest = export.run(request(run_dir, out, replay_dir, cap))
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


def _with_identity_edit(report, path, mode):
    """The replay report with one run-identity field removed or altered."""

    parent = report
    for key in path[:-1]:
        parent = parent[key]
    value = parent[path[-1]]
    if mode == "missing":
        parent.pop(path[-1])
    else:
        # Exact int preserves the test's bool/subclass boundary.
        parent[path[-1]] = value + 1 if type(value) is int else "different"  # pylint: disable=unidiomatic-typecheck
    return report


class Artifacts(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-export-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def _exported(self):
        _summary, records, run_dir = smoke_run()
        manifest, out = export_of(run_dir, self.root)
        positives = [r for r in records if views.is_positive(r)]
        return manifest, out, records, positives

    def test_the_tables_count_records_and_positives_and_the_evidence_is_complete(self):
        manifest, out, records, positives = self._exported()
        self.assertEqual(manifest["tables"]["positives"], len(positives))
        self.assertEqual(manifest["tables"]["records"], len(records))
        self.assertEqual(manifest["tables"]["dispositions"]["exported"], len(positives))
        evidence = [r for _n, r in oc.read_jsonl(out / export.EVIDENCE_PATH)]
        self.assertEqual(evidence, records)

    def test_split_rows_cover_exactly_the_positives_with_prompt_and_completion(self):
        _manifest, out, _records, positives = self._exported()
        rows = {s: [r for _n, r in oc.read_jsonl(out / f"sft/{s}.jsonl")] for s in lineage.SPLITS}
        self.assertEqual(sum(len(v) for v in rows.values()), len(positives))
        keys = {frozenset(r) for v in rows.values() for r in v}
        self.assertEqual(keys, {frozenset({"prompt", "completion"})})

    def test_consumer_rows_and_the_freeze_name_the_held_out_positives(self):
        _manifest, out, _records, positives = self._exported()
        agoge = [r for _n, r in oc.read_jsonl(out / export.AGOGE_PATH)]
        self.assertEqual(len(agoge), len(positives))
        self.assertEqual(set(agoge[0]), {"canonical_id", "lineage_id", "group_id", "split", "text", "completion_start_char"})
        freeze = json.loads((out / export.FREEZE_PATH).read_text())
        held_out = [r["canonical_id"] for r in agoge if r["split"] == "held_out"]
        self.assertEqual(freeze["canonical_ids"], held_out)

    def test_the_manifest_pins_every_file_and_reports_a_blocked_complete_pipeline(self):
        manifest, out, _records, _positives = self._exported()
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
        stamp_replay(run_dir, replay_dir)
        first, out_a = export_of(run_dir, self.root / "a", replay_dir)
        second, out_b = export_of(run_dir, self.root / "b", replay_dir)
        self.assertEqual(first["files"], second["files"])
        for relative in first["files"]:
            self.assertEqual((out_a / relative).read_bytes(), (out_b / relative).read_bytes())
        self.assertEqual(
            (out_a / export.MANIFEST_FILENAME).read_bytes(),
            (out_b / export.MANIFEST_FILENAME).read_bytes(),
        )
        self.assertEqual(first["replay"], "passed")
        self.assertNotIn(cv.BLOCKER_REPLAY_NOT_RUN, first["admission"]["blockers"])

    def test_manifest_write_preserves_exact_decimal_metadata(self):
        precise_timeout = "2.0000000000000000000001"
        summary, records, _run_dir = smoke_run()
        run = copy.deepcopy(summary)
        run["timeout_s"] = ExactJSONFloat(precise_timeout)
        corpus = export._Corpus(run, records, None, None)
        manifest = export._manifest(
            request(self.root / "unused-run", self.root / "unused-export"),
            corpus,
            {},
        )

        export._write_json(self.root, export.MANIFEST_FILENAME, manifest)

        persisted = load_strict_json(
            (self.root / export.MANIFEST_FILENAME).read_bytes()
        )
        self.assertEqual(
            exact_fraction(persisted["run"]["timeout_s"]),
            exact_fraction(run["timeout_s"]),
        )

    def test_request_refusals(self):
        _summary, _records, run_dir = smoke_run()
        with refusal(self, cv.FINDING_RUN_FILE_MISSING):
            export.run(request(self.root / "nowhere", self.root / "out"))
        (self.root / "taken").mkdir()
        with refusal(self, cv.FINDING_DESTINATION_EXISTS):
            export.run(request(run_dir, self.root / "taken"))
        with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW):
            export.run(request(run_dir, self.root / "outputs" / "raw" / "x"))
        with refusal(self, cv.FINDING_CAP_OUT_OF_DOMAIN):
            export.run(request(run_dir, self.root / "out", None, 0))
        with refusal(self, cv.FINDING_REPLAY_FILE_MISSING):
            export.run(request(run_dir, self.root / "out", self.root / "no-replay"))


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
            ("digest", lambda r: r["result"]["phases"]["mutant"]["public"][0].update(
                status="pass"), False),
            ("verdict", lambda r: r["result"].update(outcome=cv.OUTCOME_REJECTED), True),
            ("label", lambda r: r["scenario"].update(outcome="accepted"), True),
        )
        for name, tamper, restamped in cases:
            with self.subTest(name=name), refusal(self, cv.FINDING_EXPORT_INTEGRITY, "integrity"):
                run_dir = self.tampered_run(tamper, restamped, name)
                export.run(request(run_dir, self.root / f"out-{name}"))

    def test_a_failed_or_missing_replay_of_a_positive_refuses_but_ineligible_records_never_do(self):
        _summary, _records, run_dir = smoke_run()
        replay_dir = self.root / "replay"
        replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, replay_dir, 5.0))
        stamp_replay(run_dir, replay_dir)
        report_path = replay_dir / replay.REPLAY_FILENAME
        report = json.loads(report_path.read_text())
        entry = next(e for e in report["records"] if e["status"] == "replayed")
        entry["code"] = cv.REPLAY_ROWS_MISMATCH
        report_path.write_text(json.dumps(report))
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, cv.EXPORT_REPLAY_RUN_IDENTITY_MISMATCH):
            export.run(request(run_dir, self.root / "out", replay_dir))
        report["records"].remove(entry)
        report_path.write_text(json.dumps(report))
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, cv.EXPORT_REPLAY_RUN_IDENTITY_MISMATCH):
            export.run(request(run_dir, self.root / "out", replay_dir))
        manifest, _out = export_of(run_dir, self.root / "plain")
        self.assertGreater(manifest["tables"]["outcomes"]["rejected"], 0)
        self.assertGreater(manifest["tables"]["oracle_statuses"]["provisional"], 0)
        self.assertEqual(
            manifest["tables"]["dispositions"]["exported"], manifest["tables"]["positives"]
        )

    def test_a_lineage_in_two_splits_or_a_moved_split_refuses(self):
        def move(record):
            block = record["provenance"]["split_lineage"]
            block["split"] = "validation" if block["split"] != "validation" else "train"

        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, cv.EXPORT_SPLIT_REDERIVATION_MISMATCH):
            export.run(request(self.tampered_run(move), self.root / "out-moved"))
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
            export.run(request(run_dir, self.root / "out-cross"))

    def test_replay_identity_requires_every_run_field(self):
        _summary, _records, run_dir = smoke_run()
        replay_dir = self.root / "replay"
        replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, replay_dir, 5.0))
        baseline = stamp_replay(run_dir, replay_dir)
        paths = [("run_identity",)] + [
            ("run_identity", k) for k in
            ("candidates_sha256", "seed", "produced_at", "harness_sha256")
        ] + [("run_identity", "catalog", k) for k in ("catalog_id", "programs_sha256")]
        for path, mode in itertools.product(paths, ("missing", "changed")):
            report = _with_identity_edit(copy.deepcopy(baseline), path, mode)
            (replay_dir / replay.REPLAY_FILENAME).write_text(json.dumps(report))
            with self.subTest(path=path, mode=mode), refusal(
                self, cv.FINDING_EXPORT_INTEGRITY, "REPLAY_RUN_IDENTITY_MISMATCH"
            ):
                export.run(request(run_dir, self.root / "out", replay_dir))

    def test_malformed_replay_reports_are_coded_refusals(self):
        _summary, _records, run_dir = smoke_run()
        replay_dir = self.root / "replay"
        replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, replay_dir, 5.0))
        baseline = stamp_replay(run_dir, replay_dir)
        malformed = ["{", "[]", json.dumps({**baseline, "records": [None]}),
                     json.dumps({**baseline, "records": [{"record_id": []}]}),
                     json.dumps({**baseline, "records": baseline["records"] * 2})]
        for text in malformed:
            (replay_dir / replay.REPLAY_FILENAME).write_text(text)
            with self.subTest(text=text[:50]), refusal(
                self, cv.FINDING_EXPORT_INTEGRITY, "REPLAY_FILE_MALFORMED"
            ):
                export.run(request(run_dir, self.root / "out", replay_dir))

    def test_nonpassed_replay_status_keeps_the_blocker(self):
        _summary, _records, run_dir = smoke_run()
        replay_dir = self.root / "replay"
        replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, replay_dir, 5.0))
        baseline = stamp_replay(run_dir, replay_dir)
        for status in ("failed", "nothing_to_replay"):
            report = {**baseline, "status": status}
            (replay_dir / replay.REPLAY_FILENAME).write_text(json.dumps(report))
            with refusal(self, cv.FINDING_EXPORT_INTEGRITY):
                export_of(run_dir, self.root / status, replay_dir)

    def test_catalog_digest_and_policy_bind_the_run(self):
        for field in ("digest", "missing_policy", "different_policy"):
            run_dir, _records = run_copy(self.root / field)
            path = run_dir / generate.RUN_FILENAME
            meta = json.loads(path.read_text())
            if field == "digest":
                meta["catalog"]["programs_sha256"] = "0" * 64
            elif field == "missing_policy":
                meta["split_policy"] = None
            else:
                meta["split_policy"]["seed"] += 1
            path.write_text(json.dumps(meta))
            with self.subTest(field=field), refusal(
                self, cv.FINDING_EXPORT_INTEGRITY, "EXPORT_CATALOG_MISMATCH"
            ):
                export.run(request(run_dir, self.root / "out"))

    def test_catalog_lineage_and_group_cannot_be_relabelled(self):
        for key in ("lineage_id", "group_id", "policy_sha256"):
            def tamper(record):
                record["provenance"]["split_lineage"][key] = "forged"
            run_dir = self.tampered_run(tamper, name=key)
            with self.subTest(key=key), refusal(
                self, cv.FINDING_EXPORT_INTEGRITY, cv.EXPORT_SPLIT_REDERIVATION_MISMATCH
            ):
                export.run(request(run_dir, self.root / "out"))

    def test_run_summary_detects_truncation_and_count_tampering(self):
        for field in ("truncated", "records", "outcomes", "oracle_statuses"):
            run_dir, records = run_copy(self.root / field)
            path = run_dir / generate.RUN_FILENAME
            meta = json.loads(path.read_text())
            if field == "truncated":
                (run_dir / generate.CANDIDATES_FILENAME).unlink()
                oc.write_jsonl(run_dir / generate.CANDIDATES_FILENAME, records[:-1])
            elif field == "records":
                meta[field] += 1
            else:
                meta[field] = {}
            path.write_text(json.dumps(meta))
            with self.subTest(field=field), refusal(
                self, cv.FINDING_EXPORT_INTEGRITY, "RUN_SUMMARY_MISMATCH"
            ):
                export.run(request(run_dir, self.root / "out"))

    def test_missing_family_fields_refuse_without_tracebacks(self):
        paths = ("result.phases", "result.phases.original", "result.phases.mutant.public",
                 "result.broken_sha256", "scenario.source.module_sha256",
                 "scenario.broken_program.files.program.py",
                 "candidate_prediction.predicted_repair",
                 "result.public_failure_evidence", "provenance.split_lineage")
        for index, (path, mode) in enumerate(itertools.product(paths, ("missing", "wrong_type"))):
            def remove(record):
                keys = path.replace("program.py", "PROGRAM").split(".")
                parent = record
                for key in keys[:-1]:
                    parent = parent[key]
                key = keys[-1].replace("PROGRAM", "program.py")
                if mode == "missing":
                    parent.pop(key)
                else:
                    parent[key] = 42
                record["provenance"]["record_sha256"] = oc.record_digest(record)
            run_dir = self.tampered_run(remove, False, str(index))
            with self.subTest(path=path), refusal(
                self, cv.FINDING_EXPORT_INTEGRITY, cv.EXPORT_RECORD_FAILS_CONTRACT
            ):
                export.run(request(run_dir, self.root / "out"))



class DedupAndAdmission(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-export-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_exact_duplicates_and_the_lineage_cap_are_dispositions_not_refusals(self):
        summary, records, run_dir = smoke_run()
        positives = [r for r in records if views.is_positive(r)]
        twin = copy.deepcopy(positives[0])
        twin["id"] += "-twin"
        corpus = export._Corpus(summary, records, None, None, positives=positives + [twin])
        export._project(corpus)
        self.assertEqual(corpus.dispositions[cv.EXPORT_DUPLICATE_EXACT], 1)
        manifest, _out = export_of(run_dir, self.root / "cap", cap=1)
        self.assertLessEqual(max(manifest["tables"]["per_lineage_exported"].values()), 1)
        self.assertIn(cv.EXPORT_LINEAGE_CAP_APPLIED, manifest["tables"]["dispositions"])

    def test_admission_blockers_never_include_an_evaluation_limitation(self):
        cleared = export.Gates(True, True, True, True)
        self.assertEqual(
            export.admission_blockers(cleared, replay_passed=True, exported_rows=3), []
        )
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
        code = cli.run(["export", "--run", str(run_dir), "--catalog", str(FIXTURE_CATALOG),
                        "--out", str(self.root / "cli-out"), "--json"])
        self.assertEqual(code, 0)
        self.assertTrue((self.root / "cli-out" / export.MANIFEST_FILENAME).is_file())
    def test_export_cli_requires_catalog(self):
        _summary, _records, run_dir = smoke_run()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            cli.run(["export", "--run", str(run_dir), "--out", str(self.root / "out")])



class ConsumerProbe(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="code-repair-probe-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rows = self.root / "agoge.jsonl"
        prompt = 'prompt' + probe.SEPARATOR
        self.rows.write_text(json.dumps({'canonical_id': 'one', 'text': prompt + 'code',
                                        'completion_start_char': len(prompt)}) + '\n')
        self.manifest = self.root / "MANIFEST.json"
        self.meta = {
            "run": {"split_policy": {"seed": 1}},
            "files": {export.AGOGE_PATH: hashlib.sha256(self.rows.read_bytes()).hexdigest()},
            "tables": {"dispositions": {"exported": 1}},
        }
        self.argv = [str(self.rows), "--manifest", str(self.manifest), "--json"]
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in (("_load_proof", {"frozen_split_records": 1, "records": ["one"]}),
                            ("_spec", "spec"), ("_split_agreement", {"agree": True})):
            self.stack.enter_context(mock.patch.object(probe, name, return_value=value))

    def run_probe(self, extra=()):
        self.manifest.write_text(json.dumps(self.meta))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = probe.main(self.argv + list(extra))
        return code, json.loads(output.getvalue())

    def test_requested_steps_must_succeed(self):
        self.assertEqual(self.run_probe()[0], 0)
        cases = (("_config", ["--config", "missing"]),
                 ("_label_report", ["--config", "config"]),
                 ("_freeze", ["--freeze-into", str(self.root / "frozen")]))
        for step, extra in cases:
            with mock.patch.object(probe, "_config", return_value={"model_id": "fake"}):
                with mock.patch.object(probe, step, side_effect=ValueError("requested failure")):
                    code, report = self.run_probe(extra)
            self.assertEqual(code, 1)
            self.assertFalse(report["passed"])
            self.assertIn("freeze" if step == "_freeze" else "labels", report["failed_steps"])

    def test_manifest_binds_input_bytes_and_row_count(self):
        for field in ("digest", "count"):
            if field == "digest":
                self.meta["files"][export.AGOGE_PATH] = "0" * 64
            else:
                self.meta["files"][export.AGOGE_PATH] = hashlib.sha256(
                    self.rows.read_bytes()).hexdigest()
                self.meta["tables"]["dispositions"]["exported"] = 2
            code, report = self.run_probe()
            self.assertEqual(code, 1)
            self.assertIn("manifest", report["failed_steps"])

    def test_null_policy_skips_split_but_requested_freeze_fails(self):
        self.meta["run"]["split_policy"] = None
        code, report = self.run_probe()
        self.assertEqual(code, 0)
        self.assertEqual(report["split_agreement"]["status"], "not evaluated: no split policy")
        code, report = self.run_probe(["--freeze-into", str(self.root / "frozen")])
        self.assertEqual(code, 1)
        self.assertIn("freeze", report["failed_steps"])


if __name__ == "__main__":
    unittest.main()
