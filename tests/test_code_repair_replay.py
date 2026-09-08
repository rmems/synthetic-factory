#!/usr/bin/env python3
"""Replay: real re-execution catches what stored digests and re-derived verdicts cannot."""

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (  # noqa: E402
    FIXTURE_CATALOG, catalog, cli, envelope, executor, fixture, generate, oc, refusal, smoke_run,
    verify, views, vocabulary as cv,
)
from code_repair import replay  # noqa: E402

RUNNER = executor.Executor(timeout_s=5.0)


def positives():
    _summary, records, _run_dir = smoke_run()
    return [r for r in records if views.is_positive(r)]


def restamp(record):
    """Recompute every stored digest so the record is self-consistent again."""

    result = record["result"]
    result["evidence_sha256"] = verify.result_hash(result["phases"])
    record["provenance"]["record_sha256"] = envelope.record_digest(record)
    return record


def consistently_forged():
    """A record whose "broken" program behaves exactly like the original (a trailing comment is
    its only difference), while its stored rows, hashes and verdict all claim a failure."""

    record = copy.deepcopy(positives()[0])
    behaves_like_original = views.completion_of(record) + "# forged\n"
    record["scenario"]["broken_program"]["files"]["program.py"] = behaves_like_original
    record["scenario"]["broken_program"]["sha256"] = catalog.sha256_text(behaves_like_original)
    record["result"]["broken_sha256"] = catalog.sha256_text(behaves_like_original)
    return restamp(record)


class RealReplay(unittest.TestCase):
    def test_every_positive_of_the_smoke_run_replays_and_passes(self):
        _summary, records, run_dir = smoke_run()
        out = Path(tempfile.mkdtemp(prefix="code-repair-replay-")) / "replay"
        self.addCleanup(shutil.rmtree, out.parent, True)
        report = replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, out, 5.0))
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["counts"]["positives"], len(positives()))
        self.assertEqual(report["counts"]["failed"], 0)
        self.assertEqual(report["counts"]["not_replayed"], len(records) - len(positives()))
        listed = {e["record_id"]: e for e in report["records"]}
        rejected = next(r for r in records if r["result"]["outcome"] == cv.OUTCOME_REJECTED)
        self.assertEqual(listed[rejected["id"]]["status"], "not_replayed")
        self.assertEqual(listed[rejected["id"]]["reason"], "natural ineligibility")
        self.assertTrue((out / replay.REPLAY_FILENAME).is_file())
        self.assertTrue((out / replay.REPLAY_LOG_FILENAME).is_file())
        self.assertEqual(json.loads((out / replay.REPLAY_FILENAME).read_text())["status"], "passed")


class Forgeries(unittest.TestCase):
    def test_a_consistently_forged_record_passes_every_stored_check_but_not_replay(self):
        forged = consistently_forged()
        where = forged["id"]
        findings = oc.check_envelope(forged, where) + oc.check_digest(forged, where)
        self.assertEqual(findings, [])
        self.assertEqual(oc.curation_eligible(forged, findings), (True, []))
        self.assertTrue(views.is_positive(forged))
        self.assertEqual(views.view_findings(forged, views.sft_row(forged)), [])
        entry = replay.replay_record(forged, fixture(), RUNNER)
        self.assertEqual(entry["code"], cv.REPLAY_ROWS_MISMATCH)
        self.assertIn("mutant", entry["detail"])

    def test_a_repair_that_is_not_the_pinned_original_is_a_text_mismatch(self):
        forged = copy.deepcopy(positives()[0])
        broken = forged["scenario"]["broken_program"]["files"]["program.py"]
        forged["candidate_prediction"]["predicted_repair"]["files"]["program.py"] = broken
        forged["candidate_prediction"]["predicted_repair"]["sha256"] = catalog.sha256_text(broken)
        forged["result"]["repaired_sha256"] = catalog.sha256_text(broken)
        restamp(forged)
        self.assertTrue(views.is_positive(forged))
        entry = replay.replay_record(forged, fixture(), RUNNER)
        self.assertEqual(entry["code"], cv.REPLAY_TEXT_MISMATCH)
        self.assertIn("pinned original", entry["detail"])

    def test_drifts_of_the_catalog_harness_and_interpreter_are_coded(self):
        base = positives()[0]
        cases = (
            (cv.REPLAY_CATALOG_DRIFT, lambda r: r["scenario"]["source"].update(module_sha256="0" * 64)),
            (cv.REPLAY_CATALOG_DRIFT, lambda r: r["scenario"]["source"]["upstream"].update(commit="beef")),
            (cv.REPLAY_HARNESS_DRIFT, lambda r: r["oracle"]["fingerprint"].update(harness_sha256="0" * 64)),
            (cv.REPLAY_ENVIRONMENT_DRIFT, lambda r: r["oracle"]["fingerprint"].update(python="2.7")),
            (cv.REPLAY_TEXT_MISMATCH, lambda r: r["result"].update(broken_sha256="0" * 64)),
        )
        for code, edit in cases:
            with self.subTest(code=code):
                record = copy.deepcopy(base)
                edit(record)
                restamp(record)
                self.assertEqual(replay.replay_record(record, fixture(), RUNNER)["code"], code)

    def test_a_verdict_that_contradicts_the_rows_is_caught_before_execution_by_the_exporter_and_by_replay(self):
        record = copy.deepcopy(positives()[0])
        record["result"]["reason_codes"] = [cv.REASON_MUTANT_FAILS_PUBLIC, cv.REASON_REPAIR_PASSES_ALL]
        restamp(record)
        self.assertEqual(replay.replay_record(record, fixture(), RUNNER)["code"], cv.REPLAY_VERDICT_MISMATCH)


class RequestsAndCli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-replay-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_request_refusals(self):
        _summary, _records, run_dir = smoke_run()
        with refusal(self, cv.FINDING_RUN_FILE_MISSING):
            replay.run(replay.ReplayRequest(self.root / "nowhere", FIXTURE_CATALOG, self.root / "out"))
        (self.root / "taken").mkdir()
        with refusal(self, cv.FINDING_DESTINATION_EXISTS):
            replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, self.root / "taken"))
        with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW):
            replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, self.root / "outputs" / "raw" / "x"))

    def test_the_cli_reports_a_forged_run_with_exit_one_and_a_clean_run_with_exit_zero(self):
        forged_dir = self.root / "forged"
        forged_dir.mkdir()
        oc.write_jsonl(forged_dir / generate.CANDIDATES_FILENAME, [consistently_forged()])
        code = cli.run(["replay", "--run", str(forged_dir), "--catalog", str(FIXTURE_CATALOG),
                        "--out", str(self.root / "forged-replay"), "--timeout-s", "5", "--json"])
        self.assertEqual(code, 1)
        report = json.loads((self.root / "forged-replay" / replay.REPLAY_FILENAME).read_text())
        self.assertEqual(report["counts"]["failed_by_code"], {cv.REPLAY_ROWS_MISMATCH: 1})
        _summary, _records, run_dir = smoke_run()
        code = cli.run(["replay", "--run", str(run_dir), "--catalog", str(FIXTURE_CATALOG),
                        "--out", str(self.root / "clean-replay"), "--timeout-s", "5"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
