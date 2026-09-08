#!/usr/bin/env python3
"""The agent surface: exit codes, ``--json`` shapes, refusals as messages (in-process)."""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (  # noqa: E402
    FIXTURE_CATALOG, PINNED_AT, REPO, SEED, cli, generate, smoke_run, vocabulary as cv,
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
        self.assertEqual(summary["outcomes"], {"accepted": 2, "rejected": 3})
        code, text, _err = invoke(["render", str(out), f"pfr-{SEED}-00000", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(text)
        self.assertEqual(set(payload["sft"]), {"prompt", "completion"})
        self.assertEqual(payload["leak_findings"], [])
        self.assertEqual(len(payload["sha256"]["record"]), 64)
        code, text, _err = invoke(["render", str(out), f"pfr-{SEED}-00000"])
        self.assertEqual(code, 0)
        self.assertIn("### prompt\n", text)
        self.assertIn("### completion\n", text)
        code, _text, err = invoke(["generate", "--catalog", str(FIXTURE_CATALOG), "--seed", "1", "--count", "1", "--out", str(out)])
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith(cv.FINDING_DESTINATION_EXISTS))

    def test_render_refuses_a_rejected_record_with_its_reasons(self):
        _summary, _records, run_dir = smoke_run()
        code, text, _err = invoke(["render", str(run_dir), f"pfr-{SEED}-00003", "--json"])
        self.assertEqual(code, 1)
        finding = json.loads(text)["findings"][0]
        self.assertEqual(finding["code"], cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE)
        self.assertEqual(finding["reason_codes"], [cv.REASON_MUTANT_TIMEOUT])
        code, _text, err = invoke(["render", str(run_dir), "pfr-0-99999"])
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith(cv.FINDING_RECORD_NOT_FOUND))
        code, _text, err = invoke(["render", str(run_dir / "missing"), "x"])
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith(cv.FINDING_RUN_FILE_MISSING))

    def test_the_entry_script_compiles_and_names_the_package(self):
        source = (REPO / "pipelines" / "code_repair_cli.py").read_text(encoding="utf-8")
        compile(source, "code_repair_cli.py", "exec")
        self.assertIn("from code_repair import cli", source)
        self.assertEqual(generate.RUN_FORMAT, "code-repair-run/1")


if __name__ == "__main__":
    unittest.main()
