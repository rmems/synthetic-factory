#!/usr/bin/env python3
"""CSV mill package: catalog pins, AST extract, generate, CLI, no leftover mills."""

from __future__ import annotations

import ast
import contextlib
import csv as stdlib_csv
import importlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COMMITTED = REPO / "config" / "csv"
FIXTURE = REPO / "tests" / "fixtures" / "csv"
LEGACY_REF = "origin/legacy-mill-lane"
LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
LEGACY_MILL = "experiments/mill_leftover_leftover_leftover_csv_r114.py"
FIRST_SLUG = "xlsx-definedname-leftover-vs-usedrange"
FIRST_PLANT = f"csv_r114:{FIRST_SLUG}"

from pipelines.csv_mill import catalog, cli, generate  # noqa: E402
from pipelines.csv_mill._contract import (  # noqa: E402
    FACTORY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PLANT_NOT_FOUND,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_USAGE,
    GENERATOR,
    LEGACY_SOURCE,
    PAIR_KEYS,
    RECORD_PREFIX,
    REVIEWED_HOME,
    CsvRefusal,
)
from pipelines.record_kind import classify_kind  # noqa: E402
from pipelines.validate_run import check_episode  # noqa: E402


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def _git_show(path: str) -> str | None:
    executable = shutil.which("git")
    if executable is None:
        return None
    try:
        proc = subprocess.run(
            [executable, "show", f"{LEGACY_COMMIT}:{path}"],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _dict_source(pairs: list[dict[str, str]], **consts: object) -> str:
    lines = [f"{name} = {value!r}" for name, value in consts.items()]
    lines.append("PAIRS = [")
    for pair in pairs:
        args = ", ".join(f"{key}={pair[key]!r}" for key in PAIR_KEYS)
        lines.append(f"    dict({args}),")
    lines.append("]")
    return "\n".join(lines) + "\n"


TINY_PAIR = {
    "slug": "xlsx-definedname-leftover-vs-usedrange",
    "fail": "xls-definedname-handoff",
    "mod": "xldn",
    "drop": "xlsdn",
    "keep": "definedNames",
    "naive": "usedRange",
    "stack": "xlsx leftover leftover leftover definedNames",
    "drop_stack": "XLS definedName BIFF",
    "doc": (
        "https://learn.microsoft.com/en-us/dotnet/api/"
        "documentformat.openxml.spreadsheet.definednames"
    ),
    "doc2": (
        "https://learn.microsoft.com/en-us/dotnet/api/"
        "documentformat.openxml.spreadsheet.definedname"
    ),
    "domain": "xlsx-definedname-leftover-vs-usedrange",
    "ticket": "XLS-DN-114",
    "test_ok": "test_xldn",
    "test_fail": "test_xlsdn",
    "short": "xldn",
    "dshort": "xlsdn",
    "first_wrong": "skip_dn",
}


class RuntimeExecutionVisitor(ast.NodeVisitor):
    """Collect source-execution calls and runpy imports without executing source."""

    def __init__(self):
        self.hits = []

    def visit_Import(self, node):
        self.hits.extend(alias.name for alias in node.names if alias.name.split(".")[0] == "runpy")

    def visit_ImportFrom(self, node):
        if (node.module or "").split(".")[0] == "runpy":
            self.hits.append(node.module)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval"}:
            self.hits.append(node.func.id)
        self.generic_visit(node)


class CatalogLoading(unittest.TestCase):
    def test_stdlib_csv_is_not_the_mill_package(self):
        self.assertTrue(hasattr(stdlib_csv, "reader"))
        self.assertFalse(hasattr(stdlib_csv, "catalog"))
        self.assertEqual(REVIEWED_HOME, FACTORY)

    def test_committed_catalog_loads_sixteen_ast_extracted_plants(self):
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(loaded.catalog_id, "csv-lll-v1")
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(len(loaded.plants), 16)
        self.assertEqual(len(loaded.mills), 1)
        self.assertEqual(len({plant.plant_id for plant in loaded.plants}), 16)
        self.assertEqual(loaded.meta["source"]["method"], "git-show+ast.parse")
        self.assertEqual(loaded.meta["source"]["commit"], LEGACY_COMMIT)
        self.assertEqual([mill.mill_id for mill in loaded.mills], ["csv_r114"])
        self.assertEqual(loaded.plants[0].slug, FIRST_SLUG)
        self.assertEqual(loaded.plants[0].keep, "definedNames")
        self.assertEqual(loaded.plants[-1].slug, "xls-mulrk-leftover-vs-rk")
        self.assertEqual(loaded.plants[-1].ticket, "XLS-RK-129")

    def test_fixture_catalog_is_one_plant(self):
        loaded = catalog.load_catalog(FIXTURE)
        self.assertEqual(loaded.catalog_id, "csv-fixture-v1")
        self.assertEqual(len(loaded.plants), 1)
        self.assertEqual(loaded.plants[0].plant_id, f"csv_r0001:{FIRST_SLUG}")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="csv-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(FIXTURE, dest)
        meta_path = dest / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(CsvRefusal) as caught:
            catalog.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_PLANTS_SHA_MISMATCH)

    def test_unknown_plant_is_a_coded_refusal(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self.assertRaises(CsvRefusal) as caught:
            loaded.plant("csv_r0001:missing")
        self.assertEqual(caught.exception.code, FINDING_PLANT_NOT_FOUND)


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_dict_calls_and_prefix(self):
        source = _dict_source(
            [TINY_PAIR],
            FAC=FACTORY,
            PREFIX=RECORD_PREFIX,
            CATALOG_FIRST=7,
        )
        rows = catalog.plants_from_source(source, mill_id="csv_r0007", source="tiny_source.py")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["plant_id"], "csv_r0007:xlsx-definedname-leftover-vs-usedrange")
        self.assertEqual(rows[0]["base_round"], 7)
        self.assertEqual(rows[0]["ticket"], "XLS-DN-114")
        self.assertEqual(rows[0]["keep"], "definedNames")

    def test_plants_from_source_refuses_a_non_dict_call(self):
        source = "PAIRS = [P('xlsx')]\n"
        with self.assertRaises(CsvRefusal) as caught:
            catalog.plants_from_source(source, mill_id="csv_r0001", source="bad.py")
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)

    def test_legacy_mill_ast_matches_committed_catalog(self):
        text = _git_show(LEGACY_MILL)
        if text is None:
            self.skipTest(f"{LEGACY_REF}:{LEGACY_MILL} is not available")
        rows = catalog.plants_from_source(text, mill_id="csv_r114", source=LEGACY_MILL)
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(len(rows), 16)
        self.assertEqual([row["slug"] for row in rows], [plant.slug for plant in loaded.plants])
        self.assertEqual(
            [tuple(row[key] for key in PAIR_KEYS) for row in rows],
            [tuple(plant.pair_fields()[key] for key in PAIR_KEYS) for plant in loaded.plants],
        )
        self.assertEqual(rows[0]["base_round"], 114)
        self.assertEqual(LEGACY_SOURCE, LEGACY_MILL)

    def test_package_tree_has_no_vendored_mill_or_loop_scripts(self):
        hits = list((REPO / "pipelines" / "csv_mill").rglob("*mill*.py"))
        hits += list((REPO / "pipelines" / "csv_mill").rglob("*-loop-*.py"))
        hits += list((REPO / "config" / "csv").rglob("*.py"))
        self.assertEqual(hits, [])

    def test_package_never_executes_recovered_source(self):
        for path in (REPO / "pipelines" / "csv_mill").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            visitor = RuntimeExecutionVisitor()
            visitor.visit(tree)
            self.assertEqual(visitor.hits, [], msg=path.name)

    def test_source_execution_scan_detects_calls_and_imports(self):
        for source in (
            "import runpy",
            "from runpy import run_path",
            "f(exec('x'))",
            "eval('x')",
        ):
            with self.subTest(source=source):
                visitor = RuntimeExecutionVisitor()
                visitor.visit(ast.parse(source))
                self.assertTrue(visitor.hits)


class GeneratePairs(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="csv-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_fixture_pair_is_an_episode_and_not_hosted_grok(self):
        dest = self.root / "out"
        request = generate.GenerateRequest(
            FIXTURE, dest, plant_id=f"csv_r0001:{FIRST_SLUG}", round=3
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["pairs"], 1)
        self.assertEqual(summary["generator"], GENERATOR)
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        ok, bad = [json.loads(line) for line in lines]
        self.assertEqual(ok["id"], "cei-r03-xlsx-definedname-leftover-vs-usedrange")
        self.assertEqual(bad["id"], "cei-r03-xls-definedname-handoff")
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(classify_kind(bad), "episode")
        self.assertEqual(check_episode(ok, "ok"), [])
        self.assertEqual(check_episode(bad, "bad"), [])
        self.assertEqual(ok["meta"]["factory"], FACTORY)
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertNotEqual(ok["meta"]["generator"], "grok-4.6")
        self.assertTrue(ok["reward"]["success"])
        self.assertEqual(len(ok["steps"]), 16)
        self.assertFalse(bad["reward"]["success"])
        self.assertEqual(len(bad["steps"]), 17)
        self.assertEqual(
            ok["goal"],
            "Honor leftover leftover leftover definedNames; usedRange is not the index.",
        )
        notes = (dest / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        self.assertIn("Generator csv-mill", notes)
        self.assertIn("Not r106–r113 clones", notes)

    def test_existing_destination_is_refused(self):
        dest = self.root / "exists"
        dest.mkdir()
        request = generate.GenerateRequest(FIXTURE, dest, all_plants=True)
        with self.assertRaises(CsvRefusal) as caught:
            generate.run(request)
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_EXISTS)

    def test_destination_under_raw_is_refused(self):
        dest = self.root / "outputs" / "raw" / "csv-out"
        request = generate.GenerateRequest(FIXTURE, dest, all_plants=True)
        with self.assertRaises(CsvRefusal) as caught:
            generate.run(request)
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(dest.exists())

    def test_generate_requires_exactly_one_selector(self):
        dest = self.root / "none"
        request = generate.GenerateRequest(FIXTURE, dest)
        with self.assertRaises(CsvRefusal) as caught:
            generate.run(request)
        self.assertEqual(caught.exception.code, FINDING_USAGE)

    def test_committed_catalog_all_plants_are_episodes(self):
        dest = self.root / "all"
        summary = generate.run(generate.GenerateRequest(COMMITTED, dest, all_plants=True))
        self.assertEqual(summary["records"], 32)
        self.assertEqual(summary["pairs"], 16)
        self.assertEqual(summary["generator"], GENERATOR)
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 32)
        first = json.loads(lines[0])
        self.assertEqual(first["id"], f"cei-r114-{FIRST_SLUG}")
        for index, line in enumerate(lines):
            record = json.loads(line)
            self.assertEqual(classify_kind(record), "episode")
            self.assertEqual(check_episode(record, f"all-{index}"), [])
            self.assertEqual(record["meta"]["generator"], GENERATOR)
            self.assertNotEqual(record["meta"]["generator"], "grok-4.6")


class CliSurface(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="csv-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_check_json_on_the_fixture(self):
        code, out, err = invoke(["catalog-check", "--catalog", str(FIXTURE), "--json"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out), {
            "command": "catalog-check",
            "status": "ok",
            "catalog_id": "csv-fixture-v1",
            "plants": 1,
            "mills": 1,
            "findings": [],
        })

    def test_generate_json_writes_the_pair(self):
        dest = self.root / "cli-out"
        code, out, err = invoke(
            [
                "generate",
                "--catalog",
                str(FIXTURE),
                "--out",
                str(dest),
                "--plant",
                f"csv_r0001:{FIRST_SLUG}",
                "--json",
            ]
        )
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 2)
        self.assertTrue((dest / generate.RECORDS_FILENAME).is_file())

    def test_missing_catalog_is_exit_two_and_json_on_stdout(self):
        code, out, err = invoke(["catalog-check", "--catalog", "/nonexistent/csv", "--json"])
        self.assertEqual((code, err), (2, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "refused")
        self.assertEqual(payload["code"], "CATALOG_FILE_MISSING")


class ImportTwins(unittest.TestCase):
    def test_package_catalog_twin_is_one_object(self):
        twin = importlib.import_module("csv_mill.catalog")
        self.assertIs(twin, catalog)
        self.assertTrue(hasattr(stdlib_csv, "reader"))


if __name__ == "__main__":
    unittest.main()
