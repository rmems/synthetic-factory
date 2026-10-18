"""tup CLI: catalog-check and generate refusals, driven in process."""

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
    assert_usage_error,
    main_in_process,
    module_entry,
    refusal_object,
    scratch_dir,
    write_files,
)
from tup import cli

CHECK = "catalog-check"
GENERATE = "generate"
JSON = "--json"
OUT = "--out"
CATALOG = "--catalog"
CHECK_PROSE = "catalog-check ok: tup-v2 3237 plants / 138 families\n"


class TupCliCheckTests(unittest.TestCase):
    def test_catalog_check_prose_names_the_catalog_and_its_counts(self):
        self.assertEqual(main_in_process(cli.run, [CHECK]), (0, CHECK_PROSE, ""))

    def test_catalog_check_json_pins_the_whole_report(self):
        payload = json.loads(main_in_process(cli.run, [CHECK, JSON]).stdout)
        expected = {
            "catalog_id": "tup-v2",
            "command": CHECK,
            "families": 138,
            "findings": [],
            "plants": 3237,
            "status": "ok",
        }
        self.assertEqual(payload, expected)

    def test_main_takes_argv_and_returns_the_exit_code(self):
        self.assertEqual(main_in_process(cli.main, [CHECK]), (0, CHECK_PROSE, ""))

    def test_running_the_module_with_python_m_matches_the_package_entry(self):
        self.assertEqual(main_in_process(module_entry(cli), [CHECK]), (0, CHECK_PROSE, ""))


class TupCliCatalogRefusalTests(unittest.TestCase):
    def setUp(self):
        self.directory = scratch_dir(self) / "catalog"

    def test_a_missing_catalog_is_refused_on_stderr(self):
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory)])
        message = f"CATALOG_FILE_MISSING: missing {self.directory / 'CATALOG.json'}\n"
        self.assertEqual(result, (2, "", message))

    def test_a_catalog_without_its_families_file_is_refused_as_json(self):
        write_files(self.directory, {"CATALOG.json": "{}\n"})
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory), JSON])
        message = f"missing {self.directory / 'families.jsonl'}"
        expected = refusal_object(CHECK, "CATALOG_FILE_MISSING", message)
        self.assertEqual((result.returncode, result.stderr), (2, ""))
        self.assertEqual(json.loads(result.stdout), expected)

    def test_a_catalog_that_is_not_an_object_is_refused(self):
        write_files(self.directory, {"CATALOG.json": "[]\n", "families.jsonl": ""})
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory)])
        expected = (2, "", "CATALOG_FIELD_INVALID: CATALOG.json must be an object\n")
        self.assertEqual(result, expected)


class TupCliGenerateRefusalTests(unittest.TestCase):
    def setUp(self):
        self.dest = scratch_dir(self) / "out"

    def test_generate_without_a_selector_is_refused_as_json(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), JSON])
        message = "generate requires exactly one of --plant / --all"
        expected = refusal_object(GENERATE, "USAGE", message)
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))
        self.assertFalse(self.dest.exists())

    def test_generate_refuses_a_round_without_a_plant(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), "--all", "--round", "3"])
        self.assertEqual(result, (2, "", "USAGE: --round is only valid with --plant\n"))

    def test_generate_refuses_an_unknown_plant(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), "--plant", "tup-nope"])
        self.assertEqual(result, (2, "", "PLANT_NOT_FOUND: no tup plant 'tup-nope'\n"))

    def test_generate_refuses_an_existing_destination_as_json(self):
        self.dest.mkdir()
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), "--all", JSON])
        expected = refusal_object(GENERATE, "DESTINATION_EXISTS", f"{self.dest} already exists")
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))


class TupCliUsageTests(unittest.TestCase):
    def test_an_unknown_command_is_rejected(self):
        assert_usage_error(self, cli.run, ["catalog"], "invalid choice: 'catalog'")

    def test_a_round_must_be_an_integer(self):
        argv = [GENERATE, OUT, "unused", "--plant", "x", "--round", "r3"]
        assert_usage_error(self, cli.run, argv, "invalid int value: 'r3'")


if __name__ == "__main__":
    unittest.main()
