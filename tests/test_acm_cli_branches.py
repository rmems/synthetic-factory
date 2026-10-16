"""acm CLI: print or write an AST-extracted catalog, driven in process."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from acm import cli
from mill_cli_entry_support import (
    PIPELINES,
    REPO,
    argv_main,
    assert_usage_error,
    main_in_process,
    scratch_dir,
    script_entry,
)

SOURCE = str(REPO / "tests" / "fixtures" / "contract-drift" / "tiny-source")
WRITE = "--write"
CATALOG_KEYS = {
    "bans",
    "catalog_id",
    "extract",
    "factory",
    "family",
    "format",
    "generator",
    "id_prefix",
    "quota",
    "row_count",
    "rows",
    "rows_sha256",
    "sources",
    "steps",
}


class AcmCliPrintTests(unittest.TestCase):
    def test_print_mode_emits_the_extracted_catalog_as_json(self):
        result = main_in_process(cli.run, [SOURCE])
        payload = json.loads(result.stdout)
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(set(payload), CATALOG_KEYS)
        self.assertEqual((payload["format"], payload["family"]), ("acm-catalog/1", "acm"))
        self.assertEqual((payload["row_count"], len(payload["rows"])), (3, 3))
        self.assertEqual(payload["extract"]["method"], "ast.parse")
        self.assertFalse(payload["extract"]["exec"])

    def test_source_argument_is_required(self):
        assert_usage_error(self, cli.run, [], "the following arguments are required: source")

    def test_main_exits_zero_after_printing(self):
        result = main_in_process(argv_main(cli.main), [SOURCE])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["row_count"], 3)

    def test_running_the_file_as_a_script_prints_the_same_catalog(self):
        expected = main_in_process(cli.run, [SOURCE])
        result = main_in_process(script_entry(PIPELINES / "acm" / "cli.py"), [SOURCE])
        self.assertEqual(result, expected)


class AcmCliWriteTests(unittest.TestCase):
    def setUp(self):
        self.scratch = scratch_dir(self)

    def test_write_reports_the_row_count_and_the_resolved_destination(self):
        dest = self.scratch / "catalog"
        result = main_in_process(cli.run, [SOURCE, WRITE, str(dest)])
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(json.loads(result.stdout), {"row_count": 3, "path": str(dest)})

    def test_write_creates_only_the_catalog_file(self):
        dest = self.scratch / "catalog"
        main_in_process(cli.run, [SOURCE, WRITE, str(dest)])
        written = json.loads((dest / "CATALOG.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(path.name for path in dest.iterdir()), ["CATALOG.json"])
        self.assertEqual(written["row_count"], 3)

    def test_write_refuses_an_existing_destination_and_leaves_it_untouched(self):
        dest = self.scratch / "catalog"
        dest.mkdir()
        (dest / "keep.txt").write_text("kept\n", encoding="utf-8")
        argv = [SOURCE, WRITE, str(dest)]
        result = main_in_process(cli.run, argv)
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertIn("acm.write.dest_exists", result.stderr)
        self.assertEqual(sorted(path.name for path in dest.iterdir()), ["keep.txt"])

    def test_write_refuses_a_destination_named_like_a_mill_script(self):
        dest = self.scratch / "acm-mill-r1.py"
        result = main_in_process(cli.run, [SOURCE, WRITE, str(dest)])
        self.assertEqual(result, (1, "", "refusing to vendor acm-mill-r1.py\n"))
        self.assertFalse(dest.exists())
        self.assertFalse((dest / "CATALOG.json").exists())


if __name__ == "__main__":
    unittest.main()
