"""ewr CLI: catalog-check and generate, driven in process."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from ewr import cli
from mill_cli_entry_support import (
    PIPELINES,
    argv_main,
    assert_usage_error,
    main_in_process,
    scratch_dir,
    script_entry,
    write_files,
)

SCRIPT = PIPELINES / "ewr" / "cli.py"
CHECK = "catalog-check"
GENERATE = "generate"
JSON = "--json"
OUT = "--out"
CATALOG = "--catalog"
ROUND = "--round"
CHECK_PROSE = "catalog-check ok: 16 leftover-event pairs r40-r55\n"
CATALOG_KEYS = {
    "factory",
    "family_prefix",
    "generator",
    "mapping_pair_count",
    "n_rounds",
    "pair_count",
    "quota_per_round",
    "rounds",
    "schema_id",
    "slugs",
    "source",
    "start_round",
    "total_pairs",
}


class EwrCliReadOnlyTests(unittest.TestCase):
    def test_catalog_check_prose_counts_the_leftover_event_pairs(self):
        self.assertEqual(main_in_process(cli.run, [CHECK]), (0, CHECK_PROSE, ""))

    def test_catalog_check_json_pins_the_catalog_shape(self):
        payload = json.loads(main_in_process(cli.run, [CHECK, JSON]).stdout)
        self.assertEqual(set(payload), CATALOG_KEYS)
        self.assertEqual(payload["schema_id"], "ewr-catalog/v1")
        self.assertEqual((payload["pair_count"], payload["rounds"]), (16, list(range(40, 56))))
        counts = (payload["mapping_pair_count"], payload["total_pairs"])
        self.assertEqual(counts, (51, 67))

    def test_main_reads_its_arguments_from_sys_argv(self):
        self.assertEqual(main_in_process(argv_main(cli.main), [CHECK]), (0, CHECK_PROSE, ""))

    def test_running_the_file_as_a_script_matches_the_package_entry(self):
        expected = main_in_process(cli.run, [CHECK, JSON])
        self.assertEqual(main_in_process(script_entry(SCRIPT), [CHECK, JSON]), expected)

    def test_a_script_run_with_pipelines_on_pythonpath_matches_too(self):
        entry = script_entry(SCRIPT, pythonpath=(PIPELINES,))
        self.assertEqual(main_in_process(entry, [CHECK]), (0, CHECK_PROSE, ""))


class EwrCliCatalogRefusalTests(unittest.TestCase):
    def setUp(self):
        self.scratch = scratch_dir(self)

    def test_a_missing_catalog_is_refused_on_stderr(self):
        path = self.scratch / "CATALOG.json"
        expected = (2, "", f"ewr.catalog.field_missing: missing {path}\n")
        self.assertEqual(main_in_process(cli.run, [CHECK, CATALOG, str(path)]), expected)

    def test_a_missing_catalog_is_refused_with_json(self):
        path = self.scratch / "CATALOG.json"
        result = main_in_process(cli.run, [CHECK, CATALOG, str(path), JSON])
        expected = {"code": "ewr.catalog.field_missing", "message": f"missing {path}"}
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))

    def test_a_catalog_that_is_not_an_object_is_refused(self):
        files = {"CATALOG.json": "[]\n", "pairs.jsonl": ""}
        directory = write_files(self.scratch / "catalog", files)
        result = main_in_process(cli.run, [CHECK, CATALOG, str(directory / "CATALOG.json")])
        self.assertEqual(result, (2, "", "ewr.catalog.not_an_object: catalog must be an object\n"))


class EwrCliGenerateTests(unittest.TestCase):
    def setUp(self):
        self.dest = scratch_dir(self) / "out"

    def test_generate_prose_reports_the_episodes_and_writes_the_round(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), ROUND, "40"])
        self.assertEqual(result, (0, f"generate ok: 2 episodes -> {self.dest}\n", ""))
        self.assertTrue((self.dest / "batch-r40.jsonl").is_file())

    def test_generate_refuses_an_existing_destination(self):
        self.dest.mkdir()
        expected = (2, "", f"ewr.generate.dest_exists: destination exists: {self.dest}\n")
        self.assertEqual(main_in_process(cli.run, [GENERATE, OUT, str(self.dest)]), expected)

    def test_generate_refuses_an_unknown_round_before_creating_the_destination(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), ROUND, "56"])
        self.assertEqual(result, (2, "", "ewr.generate.round: unknown rounds: [56]\n"))
        self.assertFalse(self.dest.exists())


class EwrCliUsageTests(unittest.TestCase):
    def test_an_unknown_command_is_rejected(self):
        assert_usage_error(self, cli.run, ["catalog"], "invalid choice: 'catalog'")

    def test_a_round_must_be_an_integer(self):
        argv = [GENERATE, OUT, "unused", ROUND, "r40"]
        assert_usage_error(self, cli.run, argv, "invalid int value: 'r40'")


if __name__ == "__main__":
    unittest.main()
