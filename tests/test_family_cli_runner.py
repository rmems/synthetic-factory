"""The shared plant-family CLI runner: dispatch, exit codes, refusals and output.

``family_cli.runner`` decides every exit code the nelb, maos, pkg, ffpc and
mill ``cli`` modules return. These tests pin each branch against a probe
family whose modules are plain objects, then pin what each adopter still
chooses for itself: the catalog identity fields and where a refusal goes.
"""

import argparse
import contextlib
import importlib
import io
import json
import sys
import tempfile
import types
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple
from unittest import mock

from pipelines.family_cli import runner
from pipelines.ffpc import cli as ffpc_cli
from pipelines.maos import cli as maos_cli
from pipelines.mill import cli as mill_cli
from pipelines.nelb import cli as nelb_cli
from pipelines.oracle_grounded import envelope, refusals
from pipelines.pkg import cli as pkg_cli

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
MILL_CATALOG = REPO / "catalogs" / "mill"
PINNED_AT = "2026-09-15T00:00:00.000Z"

ROUND_CODE = "ROUND_OUT_OF_DOMAIN"
REFUSED_JSON = (
    '{"code": "ROUND_OUT_OF_DOMAIN", "command": "go", '
    '"message": "ROUND_OUT_OF_DOMAIN: round 0", "status": "refused"}\n'
)
REFUSED_TEXT = "ROUND_OUT_OF_DOMAIN: round 0\n"


class ProbeRefusal(refusals.CodedRefusal):
    CODES = frozenset({ROUND_CODE})


def capture(call, *args, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = call(*args, **kwargs)
    return code, out.getvalue(), err.getvalue()


def go_parser(*, with_json):
    parser = argparse.ArgumentParser(prog="probe")
    commands = parser.add_subparsers(dest="command", required=True)
    go = commands.add_parser("go")
    if with_json:
        go.add_argument("--json", action="store_true")
    return parser


def say_ok(_args):
    print("ok")


def refuse_round(_args):
    raise ProbeRefusal(ROUND_CODE, "round 0")


def refuse_uncoded(_args):
    raise envelope.ContractError("plain refusal")


def crash(_args):
    raise RuntimeError("not a contract refusal")


def run_go(handler, argv, **kwargs):
    parser = go_parser(with_json=kwargs.pop("with_json", True))
    return capture(runner.run_commands, parser, {"go": handler}, argv, **kwargs)


class RunCommands(unittest.TestCase):
    def test_a_returning_handler_exits_zero(self):
        self.assertEqual(run_go(say_ok, ["go"]), (runner.EXIT_OK, "ok\n", ""))
        self.assertEqual(runner.EXIT_OK, 0)

    def test_a_refusal_under_json_prints_one_sorted_object_on_stdout(self):
        self.assertEqual(run_go(refuse_round, ["go", "--json"]), (2, REFUSED_JSON, ""))
        self.assertEqual(runner.EXIT_REFUSED, 2)

    def test_a_refusal_without_json_prints_its_prose_on_stderr(self):
        self.assertEqual(run_go(refuse_round, ["go"]), (2, "", REFUSED_TEXT))

    def test_json_refusals_off_keeps_a_refusal_on_stderr_under_json(self):
        result = run_go(refuse_round, ["go", "--json"], json_refusals=False)
        self.assertEqual(result, (2, "", REFUSED_TEXT))

    def test_a_command_without_a_json_flag_reports_on_stderr(self):
        result = run_go(refuse_round, ["go"], with_json=False)
        self.assertEqual(result, (2, "", REFUSED_TEXT))

    def test_an_uncoded_contract_error_reports_a_null_code(self):
        code, out, err = run_go(refuse_uncoded, ["go", "--json"])
        self.assertEqual((code, err), (2, ""))
        self.assertEqual(
            json.loads(out),
            {"code": None, "command": "go", "message": "plain refusal", "status": "refused"},
        )

    def test_any_other_exception_propagates(self):
        with self.assertRaisesRegex(RuntimeError, "not a contract refusal"):
            run_go(crash, ["go"])

    def test_a_usage_error_exits_two_through_argparse(self):
        with self.assertRaises(SystemExit) as caught:
            run_go(say_ok, ["stop"])
        self.assertEqual(caught.exception.code, 2)


@dataclass(frozen=True)
class Plant:
    source_round: int
    record_id: str

    def as_mapping(self):
        return {"id": self.record_id, "round": self.source_round}


class RunRequest(NamedTuple):
    round_n: int
    out_dir: Path


PLANTS = (Plant(1, "fam-r01-a"), Plant(2, "fam-r02-b"))
CHECK_REPORT = {"plants": 2, "first_round": 1, "last_round": 2, "note": "ü"}
SUMMARY = {"records": 1, "destination": "fresh"}


def plants_for_round(round_n):
    chunk = tuple(plant for plant in PLANTS if plant.source_round == round_n)
    if not chunk:
        raise ProbeRefusal(ROUND_CODE, f"round {round_n}")
    return chunk


def run_probe(request):
    if request.round_n != 1:
        raise ProbeRefusal(ROUND_CODE, f"round {request.round_n}")
    return SUMMARY


def module(name, **attrs):
    made = types.ModuleType(name)
    made.__dict__.update(attrs)
    return made


CONTRACT = module(
    "probe_contract",
    SOURCE_REF="origin/probe",
    SOURCE_COMMIT="0" * 40,
    FAMILY_PREFIX="fam",
    FACTORY="fam-factory",
)
CATALOG = module(
    "probe_catalog",
    load_catalog=lambda: types.SimpleNamespace(catalog_id="fam-plants-v1", plants=PLANTS),
    catalog_check=lambda: dict(CHECK_REPORT),
    plants_for_round=plants_for_round,
)
GENERATE = module("probe_generate", RunRequest=RunRequest, run=run_probe)
IDENTITY = {
    "source_ref": "origin/probe",
    "source_commit": "0" * 40,
    "family_prefix": "fam",
    "factory": "fam-factory",
}


def record(plant):
    return {"id": plant.record_id, "zeta": "ü", "alpha": plant.source_round}


def probe_commands(**extra_identity):
    return runner.PlantCatalogCommands(
        prog="fam",
        description="Probe family commands.",
        family=runner.PlantFamily(CONTRACT, CATALOG, GENERATE, record, extra_identity),
        helps=("list the probe catalog", "check the probe catalog", "emit one probe round"),
        plant_line=lambda plant: f"{plant.source_round} {plant.record_id}",
        check_line="catalog-check ok: {plants} plants r{first_round}-r{last_round}",
    )


def indented(payload, *, ensure_ascii):
    return json.dumps(payload, ensure_ascii=ensure_ascii, indent=2, sort_keys=True) + "\n"


class PlantCatalogParser(unittest.TestCase):
    def test_the_three_subcommands_keep_their_order_and_help(self):
        parser = probe_commands().build_parser()
        self.assertEqual(
            parser.format_usage(), "usage: fam [-h] {catalog,catalog-check,generate} ...\n"
        )
        help_text = parser.format_help()
        self.assertIn("Probe family commands.", help_text)
        for line in ("list the probe catalog", "check the probe catalog", "emit one probe round"):
            self.assertIn(line, help_text)

    def test_generate_takes_round_then_out_then_json(self):
        code, out = self.help_of("generate")
        self.assertEqual(code, 0)
        usage = "usage: fam generate [-h] --round ROUND [--out OUT] [--json]\n"
        self.assertTrue(out.startswith(usage))
        self.assertIn("new destination; omit to print JSONL", out)

    def test_catalog_and_check_take_only_json(self):
        for name in ("catalog", "catalog-check"):
            with self.subTest(name=name):
                code, out = self.help_of(name)
                self.assertEqual(code, 0)
                self.assertTrue(out.startswith(f"usage: fam {name} [-h] [--json]\n"))

    def help_of(self, name):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as caught:
            probe_commands().run([name, "--help"])
        return caught.exception.code, out.getvalue()


class PlantCatalogCommands(unittest.TestCase):
    def test_catalog_json_names_the_family_and_lists_every_plant(self):
        code, out, err = capture(probe_commands(source_slice="fam/r01").run, ["catalog", "--json"])
        expected = {
            "command": "catalog",
            **IDENTITY,
            "source_slice": "fam/r01",
            "catalog_id": "fam-plants-v1",
            "plants": [plant.as_mapping() for plant in PLANTS],
        }
        self.assertEqual((code, out, err), (0, indented(expected, ensure_ascii=False), ""))

    def test_catalog_text_prints_a_header_then_one_line_per_plant(self):
        result = capture(probe_commands().run, ["catalog"])
        self.assertEqual(
            result, (0, "fam-plants-v1 fam-factory 2 plants\n1 fam-r01-a\n2 fam-r02-b\n", "")
        )

    def test_catalog_check_text_fills_the_template_from_the_report(self):
        result = capture(probe_commands().run, ["catalog-check"])
        self.assertEqual(result, (0, "catalog-check ok: 2 plants r1-r2\n", ""))

    def test_catalog_check_json_is_ascii_escaped(self):
        result = capture(probe_commands().run, ["catalog-check", "--json"])
        expected = indented({"command": "catalog-check", **CHECK_REPORT}, ensure_ascii=True)
        self.assertEqual(result, (0, expected, ""))
        self.assertIn("\\u00fc", result[1])

    def test_generate_without_out_prints_compact_unsorted_jsonl(self):
        result = capture(probe_commands().run, ["generate", "--round", "2", "--json"])
        self.assertEqual(result, (0, '{"id":"fam-r02-b","zeta":"ü","alpha":2}\n', ""))

    def test_generate_with_out_reports_the_summary(self):
        text = capture(probe_commands().run, ["generate", "--round", "1", "--out", "fresh"])
        self.assertEqual(text, (0, "generated 1 records into fresh\n", ""))
        as_json = capture(
            probe_commands().run, ["generate", "--round", "1", "--out", "fresh", "--json"]
        )
        expected = {"command": "generate", "status": "ok", "summary": SUMMARY}
        self.assertEqual(as_json, (0, indented(expected, ensure_ascii=True), ""))

    def test_a_refused_round_exits_two_both_ways(self):
        refused = '{"code": "ROUND_OUT_OF_DOMAIN", "command": "generate", '
        code, out, err = capture(probe_commands().run, ["generate", "--round", "9", "--json"])
        self.assertEqual((code, err), (2, ""))
        self.assertTrue(out.startswith(refused))
        result = capture(probe_commands().run, ["generate", "--round", "3", "--out", "fresh"])
        self.assertEqual(result, (2, "", "ROUND_OUT_OF_DOMAIN: round 3\n"))

    def test_main_exits_with_the_run_code(self):
        runs = ((["fam", "catalog-check"], 0), (["fam", "generate", "--round", "9"], 2))
        for argv, expected in runs:
            with self.subTest(argv=argv):
                sink = io.StringIO()
                with (
                    mock.patch.object(sys, "argv", argv),
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                    self.assertRaises(SystemExit) as caught,
                ):
                    probe_commands().main()
                self.assertEqual(caught.exception.code, expected)

    def test_identity_without_extras_is_the_contract_pin(self):
        family = runner.PlantFamily(CONTRACT, CATALOG, GENERATE, record)
        self.assertEqual(family.identity(), IDENTITY)


FAMILY_KEYS = frozenset({"command", "source_ref", "source_commit", "family_prefix", "factory"})
# Each catalog adopter's cli, bound by a literal import, with the identity keys it adds.
CATALOG_ADOPTERS: tuple[tuple[str, types.ModuleType, frozenset[str]], ...] = (
    ("nelb", nelb_cli, frozenset({"source_slice"})),
    ("maos", maos_cli, frozenset()),
    ("pkg", pkg_cli, frozenset()),
    ("ffpc", ffpc_cli, frozenset()),
)


class Adopters(unittest.TestCase):
    def test_each_family_lists_its_catalog_under_its_own_identity(self):
        for name, cli, extra in CATALOG_ADOPTERS:
            with self.subTest(family=name):
                code, out, err = capture(cli.run, ["catalog", "--json"])
                self.assertEqual((code, err), (0, ""))
                keys = set(json.loads(out)) - {"catalog_id", "plants"}
                self.assertEqual(keys, FAMILY_KEYS | extra)
                self.assertEqual(cli.build_parser().prog, name)

    def test_mill_keeps_a_refusal_on_stderr_under_json(self):
        code, out, err = capture(mill_cli.run, ["render", "no-such-run-dir", "any-id", "--json"])
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(err, "RUN_FILE_MISSING: missing pairs.jsonl\n")

    def test_mill_publish_prints_its_receipt_and_refuses_an_existing_destination(self):
        catalog = ["--catalog", str(MILL_CATALOG)]
        with tempfile.TemporaryDirectory() as scratch:
            run_dir, published = Path(scratch) / "run", Path(scratch) / "published"
            seeded = ["--seed", "20260915", "--count", "2", "--produced-at", PINNED_AT]
            generate = ["generate", *catalog, *seeded, "--out", str(run_dir)]
            generated = capture(mill_cli.run, generate)
            publish = ["publish", "--run", str(run_dir), *catalog, "--out", str(published)]
            first = capture(mill_cli.run, publish)
            again = capture(mill_cli.run, [*publish, "--json"])
        self.assertEqual(generated[0], 0)
        code, out, err = first
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["format"], "mill-publication/1")
        self.assertEqual(again[:2], (2, ""))
        self.assertTrue(again[2].startswith("DESTINATION_EXISTS: "))

    def test_both_import_spellings_are_one_object(self):
        with mock.patch.object(sys, "path", [str(PIPELINES), *sys.path]):
            flat = importlib.import_module("family_cli.runner")
        self.assertIs(flat, runner)
        self.assertIs(sys.modules["family_cli"], sys.modules["pipelines.family_cli"])


if __name__ == "__main__":
    unittest.main()
