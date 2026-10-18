"""kcl CLI: catalog-check, generate and hop-replay refusals, driven in process."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from kcl import cli
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

SCRIPT = PIPELINES / "kcl" / "cli.py"
CHECK = "catalog-check"
GENERATE = "generate"
HOP = "hop-replay"
JSON = "--json"
OUT = "--out"
CATALOG = "--catalog"
NOT_AN_OBJECT = "CATALOG.json must be an object"
CHECK_PROSE = "catalog-check ok: kcl-plants-v1 705 plants / 11 mills\n"


class KclCliReadOnlyTests(unittest.TestCase):
    def test_catalog_check_prose_names_the_catalog_and_its_counts(self):
        self.assertEqual(main_in_process(cli.run, [CHECK]), (0, CHECK_PROSE, ""))

    def test_catalog_check_json_pins_the_whole_report(self):
        payload = json.loads(main_in_process(cli.run, [CHECK, JSON]).stdout)
        expected = {
            "catalog_id": "kcl-plants-v1",
            "command": CHECK,
            "factory": "k8s-crashloop-factory",
            "full_plants": 705,
            "mills": 11,
            "plants": 705,
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


class KclCliCatalogRefusalTests(unittest.TestCase):
    def setUp(self):
        self.directory = scratch_dir(self) / "catalog"

    def test_a_missing_catalog_is_refused_on_stderr(self):
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory)])
        prefix = f"kcl.catalog_file_missing: {self.directory / 'CATALOG.json'} is unreadable: "
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertTrue(result.stderr.startswith(prefix))

    def test_a_catalog_that_is_not_strict_json_is_refused_on_stderr(self):
        write_files(self.directory, {"CATALOG.json": "{\n"})
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory)])
        prefix = "kcl.catalog_field_invalid: CATALOG.json is not strict JSON: "
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertTrue(result.stderr.startswith(prefix))

    def test_a_catalog_that_is_not_an_object_is_refused_as_json_on_stdout(self):
        write_files(self.directory, {"CATALOG.json": "[]\n"})
        result = main_in_process(cli.run, [CHECK, CATALOG, str(self.directory), JSON])
        expected = refusal_object(CHECK, "kcl.catalog_field_invalid", NOT_AN_OBJECT)
        self.assertEqual((result.returncode, result.stderr), (2, ""))
        self.assertEqual(json.loads(result.stdout), expected)


class KclCliGenerateRefusalTests(unittest.TestCase):
    def setUp(self):
        self.dest = scratch_dir(self) / "out"

    def test_generate_without_a_selector_is_refused_as_json(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), JSON])
        expected = refusal_object(GENERATE, "kcl.usage", "generate needs --plant, --mill, or --all")
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))
        self.assertFalse(self.dest.exists())

    def test_generate_refuses_an_unknown_plant_as_json(self):
        argv = [GENERATE, OUT, str(self.dest), "--plant", "kcl-nope:slug", JSON]
        result = main_in_process(cli.run, argv)
        message = "no plant 'kcl-nope:slug' in the catalog"
        expected = refusal_object(GENERATE, "kcl.plant_not_found", message)
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))

    def test_generate_refuses_an_unknown_mill_on_stderr(self):
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), "--mill", "kcl-nope"])
        expected = (2, "", "kcl.mill_not_found: no mill 'kcl-nope' in the catalog\n")
        self.assertEqual(result, expected)

    def test_generate_refuses_an_existing_destination(self):
        self.dest.mkdir()
        result = main_in_process(cli.run, [GENERATE, OUT, str(self.dest), "--all"])
        expected = (2, "", f"kcl.destination_exists: destination exists: {self.dest}\n")
        self.assertEqual(result, expected)


class KclCliHopReplayRefusalTests(unittest.TestCase):
    def setUp(self):
        self.dest = scratch_dir(self) / "out"

    def test_hop_replay_refuses_an_unknown_wave_before_creating_the_destination(self):
        result = main_in_process(cli.run, [HOP, OUT, str(self.dest), "--wave", "g99z"])
        self.assertEqual(result, (2, "", "kcl.unknown_wave: unknown hopper wave 'g99z'\n"))
        self.assertFalse(self.dest.exists())

    def test_hop_replay_refuses_an_existing_destination_as_json(self):
        self.dest.mkdir()
        result = main_in_process(cli.run, [HOP, OUT, str(self.dest), JSON])
        message = f"destination exists: {self.dest}"
        expected = refusal_object(HOP, "kcl.destination_exists", message)
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, expected))


class KclCliUsageTests(unittest.TestCase):
    def test_an_unknown_command_is_rejected(self):
        assert_usage_error(self, cli.run, ["catalog"], "invalid choice: 'catalog'")

    def test_hop_replay_requires_an_output_directory(self):
        assert_usage_error(self, cli.run, [HOP], "the following arguments are required: --out")


if __name__ == "__main__":
    unittest.main()
