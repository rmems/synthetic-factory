"""wsr CLI: catalog-check and generate, driven in process."""

from __future__ import annotations

import json
import shutil
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
from wsr import cli

SCRIPT = PIPELINES / "wsr" / "cli.py"
CHECK = "catalog-check"
GENERATE = "generate"
JSON = "--json"
OUT = "--out"
CATALOG = "--catalog"
ROUND = "--round"
CATALOG_KEYS = {
    "factory",
    "family_prefix",
    "generator",
    "n_rounds",
    "pair_count",
    "quota_per_round",
    "rounds",
    "schema_id",
    "slugs",
    "source",
    "start_round",
}


class WsrCliReadOnlyTests(unittest.TestCase):
    def test_catalog_check_prose_reports_ok(self):
        # Only the verdict is pinned: the round range this line prints is an
        # owner finding (it spans r41-r72, the catalog holds r41-r56 and r89-r104).
        result = main_in_process(cli.run, [CHECK])
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertTrue(result.stdout.startswith("catalog-check ok: "))

    def test_catalog_check_json_pins_the_catalog_shape(self):
        payload = json.loads(main_in_process(cli.run, [CHECK, JSON]).stdout)
        rounds = [*range(41, 57), *range(89, 105)]
        self.assertEqual(set(payload), CATALOG_KEYS)
        self.assertEqual(payload["schema_id"], "wsr-catalog/v2")
        self.assertEqual((payload["pair_count"], payload["rounds"]), (32, rounds))
        self.assertEqual(len(payload["slugs"]), 32)

    def test_main_reads_its_arguments_from_sys_argv(self):
        expected = main_in_process(cli.run, [CHECK, JSON])
        self.assertEqual(main_in_process(argv_main(cli.main), [CHECK, JSON]), expected)

    def test_running_the_file_as_a_script_matches_the_package_entry(self):
        expected = main_in_process(cli.run, [CHECK, JSON])
        self.assertEqual(main_in_process(script_entry(SCRIPT), [CHECK, JSON]), expected)

    def test_a_script_run_with_pipelines_on_pythonpath_matches_too(self):
        expected = main_in_process(cli.run, [CHECK])
        entry = script_entry(SCRIPT, pythonpath=(PIPELINES,))
        self.assertEqual(main_in_process(entry, [CHECK]), expected)


class WsrCliCatalogRefusalTests(unittest.TestCase):
    def setUp(self):
        self.directory = scratch_dir(self) / "catalog"

    def test_a_catalog_without_its_pairs_file_is_refused(self):
        self.directory.mkdir()
        catalog = Path(shutil.copy(PIPELINES / "wsr" / "CATALOG.json", self.directory))
        message = f"missing pairs file {self.directory / 'pairs.jsonl'}"
        expected = (2, "", f"wsr.catalog.field_missing: {message}\n")
        self.assertEqual(main_in_process(cli.run, [CHECK, CATALOG, str(catalog)]), expected)

    def test_a_catalog_that_is_not_an_object_is_refused_with_json(self):
        write_files(self.directory, {"CATALOG.json": "[]\n"})
        argv = [CHECK, CATALOG, str(self.directory / "CATALOG.json"), JSON]
        result = main_in_process(cli.run, argv)
        message = "catalog must be an object"
        self.assertEqual(result.stderr, f"wsr.catalog.not_an_object: {message}\n")
        expected = {"code": "wsr.catalog.not_an_object", "message": message}
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))


class WsrCliGenerateTests(unittest.TestCase):
    def setUp(self):
        self.dest = scratch_dir(self) / "out"

    def test_generate_prose_reports_the_episodes_and_writes_the_round(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), ROUND, "41"])
        self.assertEqual(result, (0, f"generate ok: 2 episodes -> {self.dest}\n", ""))
        written = sorted(path.name for path in self.dest.iterdir())
        self.assertEqual(written, ["NOTES-r41.md", "batch-r41.jsonl"])

    def test_generate_refuses_an_existing_destination(self):
        self.dest.mkdir()
        expected = (2, "", f"wsr.generate.dest_exists: destination exists: {self.dest}\n")
        self.assertEqual(main_in_process(cli.run, [GENERATE, OUT, str(self.dest)]), expected)

    def test_generate_refuses_an_unknown_round_before_creating_the_destination(self):
        argv = [GENERATE, OUT, str(self.dest), ROUND, "57", JSON]
        result = main_in_process(cli.run, argv)
        expected = {"code": "wsr.generate.round", "message": "unknown rounds: [57]"}
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))
        self.assertFalse(self.dest.exists())


class WsrCliUsageTests(unittest.TestCase):
    def test_an_unknown_command_is_rejected(self):
        assert_usage_error(self, cli.run, ["self-check"], "invalid choice: 'self-check'")

    def test_a_round_must_be_an_integer(self):
        argv = [GENERATE, OUT, "unused", ROUND, "r41"]
        assert_usage_error(self, cli.run, argv, "invalid int value: 'r41'")


if __name__ == "__main__":
    unittest.main()
