#!/usr/bin/env python3
"""The agent surface: exit codes, ``--json`` shapes, refusals as messages (in-process)."""

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import FIXTURE_CATALOG, REPO, cli, vocabulary as cv  # noqa: E402


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


class EntryScript(unittest.TestCase):
    def test_the_entry_script_compiles_and_names_the_package(self):
        source = (REPO / "pipelines" / "code_repair_cli.py").read_text(encoding="utf-8")
        compile(source, "code_repair_cli.py", "exec")
        self.assertIn("from code_repair import cli", source)


if __name__ == "__main__":
    unittest.main()
