"""qbp CLI: catalog-check, self-check and generate, driven in process."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from mill_cli_entry_support import (
    PIPELINES,
    argv_main,
    assert_usage_error,
    main_in_process,
    scratch_dir,
    script_entry,
    write_files,
)
from qbp import cli

SCRIPT = PIPELINES / "qbp" / "cli.py"
CHECK = "catalog-check"
SELF_CHECK = "self-check"
GENERATE = "generate"
JSON = "--json"
OUT = "--out"
CATALOG = "--catalog"
MILL = "qbp-mill-leftover3-r42"
CHECK_PROSE = "catalog-check ok: 100 leftover pairs across 6 mills\n"
CATALOG_KEYS = {
    "factory",
    "family_prefix",
    "generator",
    "mills",
    "n_mills",
    "pair_count",
    "pairs_sha256",
    "schema_id",
    "slugs",
    "source",
}


class QbpCliReadOnlyTests(unittest.TestCase):
    def test_catalog_check_prose_counts_pairs_and_mills(self):
        self.assertEqual(main_in_process(cli.run, [CHECK]), (0, CHECK_PROSE, ""))

    def test_catalog_check_json_pins_the_catalog_shape(self):
        payload = json.loads(main_in_process(cli.run, [CHECK, JSON]).stdout)
        self.assertEqual(set(payload), CATALOG_KEYS)
        self.assertEqual(payload["schema_id"], "qbp-catalog/v1")
        self.assertEqual((payload["n_mills"], len(payload["mills"])), (6, 6))
        self.assertEqual((payload["pair_count"], len(payload["slugs"])), (100, 100))
        self.assertEqual(payload["mills"][0], MILL)

    def test_self_check_prose_rebuilds_every_pair(self):
        expected = (0, "self-check ok: 100 pairs across 6 mills\n", "")
        self.assertEqual(main_in_process(cli.run, [SELF_CHECK]), expected)

    def test_self_check_json_reports_status_and_counts(self):
        payload = json.loads(main_in_process(cli.run, [SELF_CHECK, JSON]).stdout)
        expected = {"command": SELF_CHECK, "status": "ok", "pairs": 100, "mills": 6}
        self.assertEqual(payload, expected)

    def test_main_reads_its_arguments_from_sys_argv(self):
        self.assertEqual(main_in_process(argv_main(cli.main), [CHECK]), (0, CHECK_PROSE, ""))

    def test_running_the_file_as_a_script_matches_the_package_entry(self):
        expected = main_in_process(cli.run, [CHECK, JSON])
        self.assertEqual(main_in_process(script_entry(SCRIPT), [CHECK, JSON]), expected)

    def test_a_script_run_with_pipelines_on_pythonpath_matches_too(self):
        entry = script_entry(SCRIPT, pythonpath=(PIPELINES,))
        self.assertEqual(main_in_process(entry, [CHECK]), (0, CHECK_PROSE, ""))


class QbpCliCatalogRefusalTests(unittest.TestCase):
    def setUp(self):
        self.scratch = scratch_dir(self)

    def test_a_missing_catalog_is_refused_on_stderr(self):
        path = self.scratch / "CATALOG.json"
        expected = (2, "", f"qbp.catalog.field_missing: missing {path}\n")
        self.assertEqual(main_in_process(cli.run, [CHECK, CATALOG, str(path)]), expected)

    def test_a_missing_pairs_file_is_refused_on_stderr_and_as_json(self):
        directory = write_files(self.scratch / "catalog", {"CATALOG.json": "{}\n"})
        argv = [SELF_CHECK, CATALOG, str(directory / "CATALOG.json"), JSON]
        result = main_in_process(cli.run, argv)
        message = f"qbp.catalog.field_missing: missing {directory / 'pairs.jsonl'}"
        self.assertEqual((result.returncode, result.stderr), (2, message + "\n"))
        expected = {"code": "qbp.catalog.field_missing", "message": message}
        self.assertEqual(json.loads(result.stdout), expected)

    def test_a_catalog_that_is_not_an_object_is_refused(self):
        files = {"CATALOG.json": "[]\n", "pairs.jsonl": ""}
        directory = write_files(self.scratch / "catalog", files)
        result = main_in_process(cli.run, [CHECK, CATALOG, str(directory / "CATALOG.json")])
        self.assertEqual(result, (2, "", "qbp.catalog.not_an_object: catalog must be an object\n"))


class QbpCliGenerateTests(unittest.TestCase):
    def setUp(self):
        self.dest = scratch_dir(self) / "out"

    def test_generate_prose_reports_the_episodes_and_writes_the_batch(self):
        argv = [GENERATE, OUT, str(self.dest), "--mill", MILL, "--round", "42"]
        result = main_in_process(cli.run, argv)
        self.assertEqual(result, (0, f"generate ok: 2 episodes -> {self.dest}\n", ""))
        self.assertTrue((self.dest / MILL / "batch-r42.jsonl").is_file())

    def test_generate_refuses_an_existing_destination(self):
        self.dest.mkdir()
        expected = (2, "", f"qbp.generate.dest_exists: destination exists: {self.dest}\n")
        self.assertEqual(main_in_process(cli.run, [GENERATE, OUT, str(self.dest)]), expected)

    def test_generate_refuses_an_unknown_mill_before_creating_the_destination(self):
        argv = [GENERATE, OUT, str(self.dest), "--mill", "qbp-mill-nope", JSON]
        result = main_in_process(cli.run, argv)
        expected = {
            "code": "qbp.catalog.mill",
            "message": "qbp.catalog.mill: unknown mill qbp-mill-nope",
        }
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))
        self.assertFalse(self.dest.exists())

    def test_generate_refuses_an_unknown_round_before_creating_the_destination(self):
        argv = [GENERATE, OUT, str(self.dest), "--mill", MILL, "--round", "7"]
        result = main_in_process(cli.run, argv)
        self.assertEqual(result, (2, "", "qbp.generate.round: unknown rounds: [7]\n"))
        self.assertFalse(self.dest.exists())


class QbpCliUsageTests(unittest.TestCase):
    def test_a_command_is_required(self):
        assert_usage_error(self, cli.run, [], "the following arguments are required: command")

    def test_an_unknown_command_is_rejected(self):
        assert_usage_error(self, cli.run, ["frobnicate"], "invalid choice: 'frobnicate'")

    def test_generate_requires_an_output_directory(self):
        assert_usage_error(self, cli.run, [GENERATE], "the following arguments are required: --out")

    def test_a_round_must_be_an_integer(self):
        argv = [GENERATE, OUT, "unused", "--round", "r42"]
        assert_usage_error(self, cli.run, argv, "invalid int value: 'r42'")


if __name__ == "__main__":
    unittest.main()
