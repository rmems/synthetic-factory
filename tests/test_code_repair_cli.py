#!/usr/bin/env python3
"""The agent surface: exit codes, ``--json`` shapes, refusals as messages (in-process)."""

import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (  # noqa: E402
    FIXTURE_CATALOG, PINNED_AT, REPO, SEED, cli, envelope, generate, oc, smoke_run, views,
    vocabulary as cv,
)


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogCheck(unittest.TestCase):
    def test_the_fixture_passes_for_real_and_reports_json(self):
        code, out, _err = invoke(["catalog-check", "--catalog", str(FIXTURE_CATALOG), "--timeout-s", "5", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual((payload["status"], payload["findings"], payload["programs"]), ("ok", [], 6))

    def test_a_refusal_is_a_coded_message_and_exit_two(self):
        code, out, err = invoke(["catalog-check", "--catalog", "/nonexistent/catalog"])
        self.assertEqual((code, out), (2, ""))
        self.assertTrue(err.startswith(cv.FINDING_CATALOG_FILE_MISSING + ": "), err)

    def test_a_refusal_under_json_is_one_coded_object_on_stdout(self):
        code, out, err = invoke(["catalog-check", "--catalog", "/nonexistent/catalog", "--json"])
        self.assertEqual((code, err), (2, ""))
        payload = json.loads(out)
        self.assertEqual((payload["status"], payload["code"]), ("refused", cv.FINDING_CATALOG_FILE_MISSING))
        self.assertEqual(payload["command"], "catalog-check")


class GenerateAndRender(unittest.TestCase):
    def test_generate_writes_a_run_and_render_shows_a_positive_pair(self):
        root = Path(tempfile.mkdtemp(prefix="code-repair-cli-"))
        self.addCleanup(shutil.rmtree, root, True)
        out = root / "run"
        code, text, _err = invoke([
            "generate", "--catalog", str(FIXTURE_CATALOG), "--seed", str(SEED), "--count", "12",
            "--produced-at", PINNED_AT, "--out", str(out), "--json",
        ])
        self.assertEqual(code, 0)
        summary = json.loads(text)["summary"]
        self.assertEqual(summary["outcomes"], {"accepted": 7, "rejected": 3})
        record_id = next(r['id'] for _, r in oc.iter_jsonl(out / generate.CANDIDATES_FILENAME)
                         if views.is_positive(r))
        code, text, _err = invoke(["render", str(out), record_id, "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(text)
        self.assertEqual(set(payload["sft"]), {"prompt", "completion"})
        self.assertEqual((payload["status"], payload["findings"]), ("ok", []))
        self.assertEqual(len(payload["sha256"]["record"]), 64)
        code, text, _err = invoke(["render", str(out), record_id])
        self.assertEqual(code, 0)
        self.assertIn("### prompt\n", text)
        self.assertIn("### completion\n", text)
        code, _text, err = invoke(["generate", "--catalog", str(FIXTURE_CATALOG), "--seed", "1", "--count", "1", "--out", str(out)])
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith(cv.FINDING_DESTINATION_EXISTS))

    def test_render_refuses_a_rejected_record_with_its_reasons(self):
        _summary, records, run_dir = smoke_run()
        rejected = next(r for r in records if r['result']['reason_codes'] == [cv.REASON_MUTANT_NO_OBSERVED_FAILURE])
        code, text, _err = invoke(["render", str(run_dir), rejected['id'], "--json"])
        self.assertEqual(code, 1)
        finding = json.loads(text)["findings"][0]
        self.assertEqual(finding["code"], cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE)
        self.assertEqual(finding["reason_codes"], [cv.REASON_MUTANT_NO_OBSERVED_FAILURE])
        provisional = next(r for r in records if r['result']['oracle_status'] == cv.STATUS_PROVISIONAL)
        code, text, _err = invoke(["render", str(run_dir), provisional['id'], "--json"])
        self.assertEqual(code, 1)
        finding = json.loads(text)["findings"][0]
        self.assertEqual(finding["oracle_status"], cv.STATUS_PROVISIONAL)
        code, _text, err = invoke(["render", str(run_dir), "pfr-0-99999"])
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith(cv.FINDING_RECORD_NOT_FOUND))
        code, _text, err = invoke(["render", str(run_dir / "missing"), "x"])
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith(cv.FINDING_RUN_FILE_MISSING))

    def test_render_never_emits_a_pair_with_a_leak_finding_or_a_malformed_record(self):
        root = Path(tempfile.mkdtemp(prefix="code-repair-cli-"))
        self.addCleanup(shutil.rmtree, root, True)
        _summary, records, _run_dir = smoke_run()
        positive = next(r for r in records if views.is_positive(r))
        leaky = copy.deepcopy(positive)
        leaky["result"]["public_failure_evidence"][0]["got"] = "a fabricated failure"
        leaky["provenance"]["record_sha256"] = envelope.record_digest(leaky)
        malformed = copy.deepcopy(positive)
        malformed["id"] = "pfr-0-00001"
        del malformed["result"]["measurements"]
        oc.write_jsonl(root / generate.CANDIDATES_FILENAME, [leaky, malformed])
        code, text, _err = invoke(["render", str(root), positive["id"], "--json"])
        self.assertEqual(code, 1)
        payload = json.loads(text)
        self.assertEqual(payload["status"], "findings")
        self.assertNotIn("sft", payload)
        self.assertIn(cv.LEAK_PUBLIC_EVIDENCE_NOT_FROM_ROWS, [f["code"] for f in payload["findings"]])
        self.assertNotIn("fabricated", text)
        code, _text, err = invoke(["render", str(root), "pfr-0-00001"])
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith(cv.FINDING_RECORD_MALFORMED), err)


class EntryScript(unittest.TestCase):
    def test_the_entry_script_compiles_and_names_the_package(self):
        source = (REPO / "pipelines" / "code_repair_cli.py").read_text(encoding="utf-8")
        compile(source, "code_repair_cli.py", "exec")
        self.assertIn("from code_repair import cli", source)
        self.assertEqual(generate.RUN_FORMAT, "code-repair-run/2")


if __name__ == "__main__":
    unittest.main()
