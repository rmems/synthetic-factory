"""obs CLI: catalog-check and generate refusals, driven in process."""

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
    argv_main,
    assert_usage_error,
    main_in_process,
    module_entry,
    refusal_object,
    scratch_dir,
    write_files,
)
from obs import cli

CHECK = "catalog-check"
GENERATE = "generate"
JSON = "--json"
OUT = "--out"
CATALOG = "--catalog"
NOT_AN_OBJECT = "CATALOG.json must be an object"
CHECK_PROSE = "catalog-check ok: obs-plants-v1 631 plants / 10 mills\n"


class ObsCliCheckTests(unittest.TestCase):
    def test_catalog_check_prose_names_the_catalog_and_its_counts(self):
        self.assertEqual(main_in_process(cli.run, [CHECK]), (0, CHECK_PROSE, ""))

    def test_catalog_check_json_pins_the_whole_report(self):
        payload = json.loads(main_in_process(cli.run, [CHECK, JSON]).stdout)
        expected = {
            "catalog_id": "obs-plants-v1",
            "command": CHECK,
            "findings": [],
            "mills": 10,
            "pairs": 191,
            "plants": 631,
            "status": "ok",
        }
        self.assertEqual(payload, expected)

    def test_main_reads_its_arguments_from_sys_argv(self):
        self.assertEqual(main_in_process(argv_main(cli.main), [CHECK]), (0, CHECK_PROSE, ""))

    def test_python_m_on_the_cli_module_matches_the_package_entry(self):
        self.assertEqual(main_in_process(module_entry("obs.cli"), [CHECK]), (0, CHECK_PROSE, ""))

    def test_python_m_on_the_package_matches_the_package_entry(self):
        self.assertEqual(main_in_process(module_entry("obs"), [CHECK]), (0, CHECK_PROSE, ""))


class ObsCliCatalogRefusalTests(unittest.TestCase):
    def setUp(self):
        self.directory = scratch_dir(self) / "catalog"

    def test_a_missing_catalog_is_refused_on_stderr(self):
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory)])
        message = f"obs.catalog_file_missing: {self.directory / 'CATALOG.json'} is missing\n"
        self.assertEqual(result, (2, "", message))

    def test_a_catalog_that_is_not_strict_json_is_refused(self):
        write_files(self.directory, {"CATALOG.json": "{\n"})
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory)])
        expected = (2, "", "obs.catalog_field_invalid: CATALOG.json is not strict JSON\n")
        self.assertEqual(result, expected)

    def test_a_catalog_that_is_not_an_object_is_refused_as_json(self):
        write_files(self.directory, {"CATALOG.json": "[]\n"})
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory), JSON])
        expected = refusal_object(CHECK, "obs.catalog_field_invalid", NOT_AN_OBJECT)
        self.assertEqual((result.returncode, result.stderr), (2, ""))
        self.assertEqual(json.loads(result.stdout), expected)


class ObsCliGenerateRefusalTests(unittest.TestCase):
    def setUp(self):
        self.dest = scratch_dir(self) / "out"

    def test_generate_without_a_selector_is_refused_on_stderr(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest)])
        message = "obs.usage: generate requires exactly one of --plant / --mill / --all\n"
        self.assertEqual(result, (2, "", message))
        self.assertFalse(self.dest.exists())

    def test_generate_refuses_a_round_without_a_plant_as_json(self):
        argv = [GENERATE, OUT, str(self.dest), "--all", "--round", "3", JSON]
        result = main_in_process(cli.run, argv)
        expected = refusal_object(GENERATE, "obs.usage", "--round is only valid with --plant")
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))

    def test_generate_refuses_an_unknown_mill(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), "--mill", "obs-nope"])
        expected = (2, "", "obs.mill_not_found: no mill 'obs-nope' in the catalog\n")
        self.assertEqual(result, expected)

    def test_generate_refuses_an_existing_destination_as_json(self):
        self.dest.mkdir()
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), "--all", JSON])
        expected = refusal_object(GENERATE, "obs.destination_exists", f"{self.dest} already exists")
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))


class ObsCliUsageTests(unittest.TestCase):
    def test_an_unknown_command_is_rejected(self):
        assert_usage_error(self, cli.run, ["catalog"], "invalid choice: 'catalog'")

    def test_generate_requires_an_output_directory(self):
        assert_usage_error(self, cli.run, [GENERATE], "the following arguments are required: --out")


if __name__ == "__main__":
    unittest.main()
