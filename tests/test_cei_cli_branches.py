"""cei CLI: catalog, catalog-check and generate refusals, driven in process."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from cei import cli
from mill_cli_entry_support import (
    PIPELINES,
    argv_main,
    assert_usage_error,
    main_in_process,
    refusal_object,
    scratch_dir,
    script_entry,
    write_files,
)

SCRIPT = PIPELINES / "cei" / "cli.py"
LISTING = "catalog"
CHECK = "catalog-check"
GENERATE = "generate"
JSON = "--json"
OUT = "--out"
CATALOG = "--catalog"
NOT_AN_OBJECT = "CATALOG.json must be an object"
CHECK_PROSE = "catalog-check ok: cei-pairs-v1 89 plants / 5 mills\n"
PLANT_KEYS = {"bad", "index", "ok", "plant_id", "round", "ticket"}


class CeiCliListingTests(unittest.TestCase):
    def test_catalog_json_lists_every_pinned_plant(self):
        payload = json.loads(main_in_process(cli.run, [LISTING, JSON]).stdout)
        head = {key: payload[key] for key in ("command", "status", "catalog_id")}
        self.assertEqual(head, {"command": LISTING, "status": "ok", "catalog_id": "cei-pairs-v1"})
        self.assertEqual(len(payload["plants"]), 89)
        self.assertEqual(set(payload["plants"][0]), PLANT_KEYS)

    def test_catalog_prose_prints_one_line_per_plant(self):
        plants = json.loads(main_in_process(cli.run, [LISTING, JSON]).stdout)["plants"]
        lines = [f"{p['round']} {p['plant_id']} {p['ok']}/{p['bad']}" for p in plants]
        self.assertEqual(main_in_process(cli.run, [LISTING]), (0, "\n".join(lines) + "\n", ""))


class CeiCliCheckTests(unittest.TestCase):
    def test_catalog_check_prose_names_the_catalog_and_its_counts(self):
        self.assertEqual(main_in_process(cli.run, [CHECK]), (0, CHECK_PROSE, ""))

    def test_catalog_check_json_pins_the_whole_report(self):
        payload = json.loads(main_in_process(cli.run, [CHECK, JSON]).stdout)
        expected = {
            "catalog_id": "cei-pairs-v1",
            "command": CHECK,
            "findings": [],
            "mills": 5,
            "plants": 89,
            "status": "ok",
        }
        self.assertEqual(payload, expected)

    def test_main_reads_its_arguments_from_sys_argv(self):
        self.assertEqual(main_in_process(argv_main(cli.main), [CHECK]), (0, CHECK_PROSE, ""))

    def test_running_the_file_as_a_script_matches_the_package_entry(self):
        expected = main_in_process(cli.run, [CHECK, JSON])
        self.assertEqual(main_in_process(script_entry(SCRIPT), [CHECK, JSON]), expected)

    def test_a_script_run_with_pipelines_on_pythonpath_matches_too(self):
        entry = script_entry(SCRIPT, pythonpath=(PIPELINES,))
        self.assertEqual(main_in_process(entry, [CHECK]), (0, CHECK_PROSE, ""))


class CeiCliCatalogRefusalTests(unittest.TestCase):
    def setUp(self):
        self.directory = scratch_dir(self) / "catalog"

    def test_a_missing_catalog_is_refused_on_stderr(self):
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory)])
        message = f"cei.catalog_file_missing: {self.directory / 'CATALOG.json'} is missing\n"
        self.assertEqual(result, (2, "", message))

    def test_a_missing_catalog_is_refused_as_json_for_the_listing(self):
        result = main_in_process(cli.run, [LISTING, CATALOG, str(self.directory), JSON])
        message = f"{self.directory / 'CATALOG.json'} is missing"
        expected = refusal_object(LISTING, "cei.catalog_file_missing", message)
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))

    def test_a_catalog_that_is_not_strict_json_is_refusal_object(self):
        write_files(self.directory, {"CATALOG.json": "{\n"})
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory)])
        expected = (2, "", "cei.catalog_field_invalid: CATALOG.json is not strict JSON\n")
        self.assertEqual(result, expected)

    def test_a_catalog_that_is_not_an_object_is_refused_as_json(self):
        write_files(self.directory, {"CATALOG.json": "[]\n"})
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory), JSON])
        expected = refusal_object(CHECK, "cei.catalog_field_invalid", NOT_AN_OBJECT)
        self.assertEqual((result.returncode, result.stderr), (2, ""))
        self.assertEqual(json.loads(result.stdout), expected)


class CeiCliGenerateRefusalTests(unittest.TestCase):
    def setUp(self):
        self.dest = scratch_dir(self) / "out"

    def test_generate_without_a_selector_is_refused_on_stderr(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest)])
        expected = (2, "", "cei.usage: exactly one of plant_id, mill_id, or all_plants\n")
        self.assertEqual(result, expected)
        self.assertFalse(self.dest.exists())

    def test_generate_refuses_a_round_without_a_plant(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), "--all", "--round", "3"])
        self.assertEqual(result, (2, "", "cei.usage: round applies only with plant_id\n"))

    def test_generate_refuses_an_unknown_mill(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), "--mill", "cei-nope"])
        expected = (2, "", "cei.mill_not_found: no mill 'cei-nope' in the catalog\n")
        self.assertEqual(result, expected)

    def test_generate_refuses_an_existing_destination_as_json(self):
        self.dest.mkdir()
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), "--all", JSON])
        expected = refusal_object(GENERATE, "cei.destination_exists", f"{self.dest} already exists")
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))


class CeiCliUsageTests(unittest.TestCase):
    def test_an_unknown_command_is_rejected(self):
        assert_usage_error(self, cli.run, ["self-check"], "invalid choice: 'self-check'")

    def test_generate_requires_an_output_directory(self):
        assert_usage_error(self, cli.run, [GENERATE], "the following arguments are required: --out")


if __name__ == "__main__":
    unittest.main()
