"""dbm CLI: catalog-check and generate, driven in process."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from dbm import cli

from mill_cli_entry_support import (
    PIPELINES,
    argv_main,
    assert_usage_error,
    main_in_process,
    scratch_dir,
    script_entry,
    write_files,
)

SCRIPT = PIPELINES / "dbm" / "cli.py"
CHECK = "catalog-check"
GENERATE = "generate"
JSON = "--json"
OUT = "--out"
ROUND = "--round"
CHECK_PROSE = (
    "catalog-check ok: 17 leftover3 pairs r1260-r1276; 601 sequential leftover-mill pairs\n"
)
CATALOG_KEYS = {
    "factory",
    "family_prefix",
    "generator",
    "leftover3_slugs",
    "mill_count",
    "mill_pairs",
    "mill_paths",
    "mill_plants",
    "n_pairs",
    "quota_per_round",
    "schema_id",
    "source",
    "start_round",
}


class DbmCliReadOnlyTests(unittest.TestCase):
    def test_catalog_check_prose_counts_both_catalogs(self):
        self.assertEqual(main_in_process(cli.run, [CHECK]), (0, CHECK_PROSE, ""))

    def test_catalog_check_json_pins_the_catalog_shape(self):
        payload = json.loads(main_in_process(cli.run, [CHECK, JSON]).stdout)
        self.assertEqual(set(payload), CATALOG_KEYS)
        self.assertEqual(payload["schema_id"], "dbm-leftover3/v1")
        self.assertEqual((payload["n_pairs"], payload["start_round"]), (17, 1260))
        self.assertEqual(len(payload["leftover3_slugs"]), 34)
        counts = (payload["mill_count"], payload["mill_pairs"], payload["mill_plants"])
        self.assertEqual(counts, (9, 601, 1202))

    def test_main_reads_its_arguments_from_sys_argv(self):
        self.assertEqual(main_in_process(argv_main(cli.main), [CHECK]), (0, CHECK_PROSE, ""))

    def test_running_the_file_as_a_script_matches_the_package_entry(self):
        expected = main_in_process(cli.run, [CHECK, JSON])
        self.assertEqual(main_in_process(script_entry(SCRIPT), [CHECK, JSON]), expected)

    def test_a_script_run_with_pipelines_on_pythonpath_matches_too(self):
        entry = script_entry(SCRIPT, pythonpath=(PIPELINES,))
        self.assertEqual(main_in_process(entry, [CHECK]), (0, CHECK_PROSE, ""))


class DbmCliCatalogRefusalTests(unittest.TestCase):
    def setUp(self):
        self.directory = write_files(scratch_dir(self) / "catalog", {"list.json": "[]\n"})

    def test_a_leftover3_catalog_that_is_not_an_object_is_refused_with_json(self):
        argv = [CHECK, "--leftover3", str(self.directory / "list.json"), JSON]
        result = main_in_process(cli.run, argv)
        message = "leftover3 must be an object"
        self.assertEqual(result.stderr, f"dbm.catalog.not_an_object: {message}\n")
        expected = {"code": "dbm.catalog.not_an_object", "message": message}
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))

    def test_a_mills_catalog_that_is_not_an_object_is_refused_on_stderr(self):
        argv = [CHECK, "--mills", str(self.directory / "list.json")]
        expected = (2, "", "dbm.catalog.not_an_object: mills must be an object\n")
        self.assertEqual(main_in_process(cli.run, argv), expected)


class DbmCliGenerateTests(unittest.TestCase):
    def setUp(self):
        self.dest = scratch_dir(self) / "out"

    def test_generate_prose_reports_the_episodes_and_writes_the_round(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), ROUND, "1260"])
        self.assertEqual(result, (0, f"generate ok: 2 episodes -> {self.dest}\n", ""))
        self.assertTrue((self.dest / "batch-r1260.jsonl").is_file())

    def test_generate_refuses_an_existing_destination(self):
        self.dest.mkdir()
        expected = (2, "", f"dbm.generate.dest_exists: destination exists: {self.dest}\n")
        self.assertEqual(main_in_process(cli.run, [GENERATE, OUT, str(self.dest)]), expected)

    def test_generate_refuses_an_unknown_round_before_creating_the_destination(self):
        argv = [GENERATE, OUT, str(self.dest), ROUND, "1277", JSON]
        result = main_in_process(cli.run, argv)
        expected = {"code": "dbm.generate.round", "message": "unknown leftover3 rounds: [1277]"}
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))
        self.assertFalse(self.dest.exists())


class DbmCliUsageTests(unittest.TestCase):
    def test_an_unknown_command_is_rejected(self):
        assert_usage_error(self, cli.run, ["self-check"], "invalid choice: 'self-check'")

    def test_generate_requires_an_output_directory(self):
        assert_usage_error(self, cli.run, [GENERATE], "the following arguments are required: --out")


if __name__ == "__main__":
    unittest.main()
