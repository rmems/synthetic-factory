#!/usr/bin/env python3
"""FFD CLI: catalog-check, generate, and coded refusals."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ffd_test_support import REPO, cli
from ffd._contract import FINDING_DESTINATION_EXISTS, FINDING_DESTINATION_UNDER_RAW


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogCheck(unittest.TestCase):
    def test_committed_catalog_passes_and_reports_json(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["findings"], [])
        self.assertEqual(payload["sources"], {"leftover3": 39, "lll": 16, "hop": 9})


class Generate(unittest.TestCase):
    def test_generate_writes_a_new_destination(self):
        with tempfile.TemporaryDirectory(prefix="ffd-cli-") as tmp:
            out = Path(tmp) / "fresh"
            code, stdout, err = invoke([
                "generate", "--source", "hop", "--round", "102", "--pair", "0",
                "--out", str(out), "--json",
            ])
            self.assertEqual((code, err), (0, ""))
            payload = json.loads(stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(len(payload["summary"]["ids"]), 2)
            self.assertTrue((out / "batch-r102.jsonl").is_file())
            self.assertIn("Novel coverage:", (out / "NOTES-r102.md").read_text())

    def test_generate_refuses_raw_and_existing(self):
        raw = REPO / "outputs" / "raw" / "ffd-cli-refuse"
        code, out, err = invoke([
            "generate", "--source", "lll", "--round", "61", "--out", str(raw),
        ])
        self.assertEqual((code, out), (2, ""))
        self.assertTrue(err.startswith(FINDING_DESTINATION_UNDER_RAW + ": "), err)
        with tempfile.TemporaryDirectory(prefix="ffd-cli-exists-") as tmp:
            code, out, err = invoke([
                "generate", "--source", "lll", "--round", "61", "--out", tmp, "--json",
            ])
            self.assertEqual((code, err), (2, ""))
            payload = json.loads(out)
            self.assertEqual(payload["status"], "refused")
            self.assertEqual(payload["code"], FINDING_DESTINATION_EXISTS)


if __name__ == "__main__":
    unittest.main()
