#!/usr/bin/env python3
"""AST-extracted qbp leftover family under ``pipelines/qbp``."""

from __future__ import annotations

import ast
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import ClassVar

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from qbp import cli  # noqa: E402
from qbp import generate as gen  # noqa: E402
from qbp._contract import (  # noqa: E402
    BAN,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_GENERATE_DEST_EXISTS,
    FINDING_GENERATE_RAW_TREE,
    GENERATOR,
    HANDOFF_STEPS,
    LEGACY_COMMIT,
    MILL_SOURCES,
    N_MILLS,
    N_PAIRS,
    SUCCESS_STEPS,
    QbpRefusal,
)
from qbp.catalog import (  # noqa: E402
    ast_extract_catalog,
    ast_extract_mill,
    ast_extract_plants,
    catalog_check,
    sha256_text,
)
from raw_tree_guard import DEFAULT_RAW_OUTPUT_ROOT  # noqa: E402

QBP_DIR = REPO / "pipelines" / "qbp"
PACKAGE_FILES = ("__init__.py", "_contract.py", "catalog.py", "cli.py", "generate.py", "plants.py")


def _legacy_source(relpath: str) -> str | None:
    for spec in (f"{LEGACY_COMMIT}:{relpath}", f"origin/legacy-mill-lane:{relpath}"):
        try:
            return subprocess.check_output(["git", "show", spec], text=True, cwd=REPO)
        except subprocess.CalledProcessError:
            continue
    return None


class QbpFamilyLayoutTests(unittest.TestCase):
    def test_package_is_exactly_the_cleaned_modules(self):
        names = tuple(sorted(path.name for path in QBP_DIR.glob("*.py")))
        self.assertEqual(names, tuple(sorted(PACKAGE_FILES)))

    def test_leftover_mill_scripts_are_not_vendored(self):
        leftover = tuple(sorted(QBP_DIR.glob("qbp-mill*.py"))) + tuple(
            sorted(QBP_DIR.glob("qbp-plants*.py"))
        )
        self.assertEqual(leftover, ())
        self.assertFalse((QBP_DIR / "qbp-mill-r74.py").exists())
        self.assertFalse((REPO / "experiments" / "qbp-mill-r74.py").exists())


class QbpNeverExec(unittest.TestCase):
    BANNED_IMPORTS: ClassVar[set[str]] = {"subprocess"}
    BANNED_DEFS: ClassVar[set[str]] = {"txn", "harvest_used"}

    def test_no_banned_imports_or_defs_in_package_modules(self):
        findings = []
        for path in sorted(QBP_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in self.BANNED_IMPORTS:
                            findings.append((path.name, "import", alias.name))
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and node.module.split(".")[0] in self.BANNED_IMPORTS
                ):
                    findings.append((path.name, "import", node.module))
                elif (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name in self.BANNED_DEFS
                ):
                    findings.append((path.name, "def", node.name))
        self.assertEqual(findings, [], f"banned exec surface found: {findings}")


class QbpCatalogTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)

    def test_catalog_check_pins_the_six_mill_windows(self):
        loaded = catalog_check(root=REPO)
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(loaded.generator, GENERATOR)
        self.assertEqual(len(loaded.mills), N_MILLS)
        self.assertEqual(len(loaded.pairs), N_PAIRS)
        self.assertEqual([mill.mill_id for mill in loaded.mills], [row[0] for row in MILL_SOURCES])
        self.assertEqual(loaded.source["commit"], LEGACY_COMMIT)
        self.assertEqual(loaded.pairs[0].ok["slug"], "nats-js-max-ack-pending")
        self.assertEqual(loaded.pairs[0].round_n, 42)

    def test_banned_r41_slugs_are_absent(self):
        loaded = catalog_check(root=REPO)
        slugs = [pair.ok["slug"] for pair in loaded.pairs] + [pair.bad["slug"] for pair in loaded.pairs]
        for banned in BAN:
            self.assertNotIn(banned, slugs)

    def test_catalog_matches_legacy_ast_extract(self):
        mill_sources = {}
        plants_sources = {}
        for _mill_id, path, mill_sha, plants_path, plants_sha, _first, n_pairs in MILL_SOURCES:
            mill = _legacy_source(path)
            plants = _legacy_source(plants_path)
            if mill is None or plants is None:
                self.skipTest("legacy-mill-lane qbp sources are not available")
            self.assertEqual(sha256_text(mill), mill_sha)
            self.assertEqual(sha256_text(plants), plants_sha)
            mill_sources[path] = mill
            plants_sources[plants_path] = plants
            extracted_mill = ast_extract_mill(mill)
            self.assertEqual(extracted_mill["plants"], plants_path)
            extracted_plants = ast_extract_plants(plants)
            self.assertEqual(extracted_plants["n_pairs"], n_pairs)
        extracted = ast_extract_catalog(mill_sources, plants_sources)
        loaded = catalog_check(root=REPO)
        self.assertEqual(len(extracted["pairs"]), len(loaded.pairs))
        for raw, pair in zip(extracted["pairs"], loaded.pairs, strict=True):
            self.assertEqual(raw["mill_id"], pair.mill_id)
            self.assertEqual(raw["round"], pair.round_n)
            self.assertEqual(raw["ok"], dict(pair.ok_args))
            self.assertEqual(raw["bad"], dict(pair.bad_args))


class QbpGenerateTests(unittest.TestCase):
    def test_first_pair_is_sixteen_plus_seventeen(self):
        loaded = catalog_check(root=REPO)
        built = gen.build_pair(loaded.pairs[0])
        self.assertEqual(built.ok["id"], "qbp-r42-nats-js-max-ack-pending")
        self.assertEqual(built.bad["id"], "qbp-r42-nats-js-drop-consumer-handoff")
        self.assertEqual(len(built.ok["steps"]), SUCCESS_STEPS)
        self.assertEqual(len(built.bad["steps"]), HANDOFF_STEPS)
        self.assertTrue(built.ok["reward"]["success"])
        self.assertFalse(built.bad["reward"]["success"])
        self.assertIn("Novel coverage:", built.notes)
        self.assertEqual(built.ok["meta"]["factory"], FACTORY)
        self.assertEqual(built.ok["meta"]["generator"], GENERATOR)

    def test_every_catalog_pair_builds(self):
        loaded = catalog_check(root=REPO)
        built = gen.build_catalog(loaded)
        self.assertEqual(len(built), N_PAIRS)
        ids = [item.ok["id"] for item in built] + [item.bad["id"] for item in built]
        self.assertEqual(len(set(ids)), 2 * N_PAIRS)
        self.assertTrue(all(item.ok["id"].startswith(f"qbp-r{item.round_n}-") for item in built))

    def test_generate_writes_a_new_tree_and_refuses_clobber(self):
        loaded = catalog_check(root=REPO)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "qbp-out"
            written = gen.generate(
                dest,
                catalog=loaded,
                mill_id="qbp-mill-leftover3-r42",
                rounds=(42,),
            )
            self.assertEqual(len(written), 1)
            batch = dest / "qbp-mill-leftover3-r42" / "batch-r42.jsonl"
            notes = dest / "qbp-mill-leftover3-r42" / "NOTES-r42.md"
            self.assertTrue(batch.is_file())
            self.assertTrue(notes.is_file())
            lines = batch.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["id"], written[0].ok["id"])
            with self.assertRaises(QbpRefusal) as raised:
                gen.generate(
                    dest,
                    catalog=loaded,
                    mill_id="qbp-mill-leftover3-r42",
                    rounds=(42,),
                )
            self.assertEqual(raised.exception.code, FINDING_GENERATE_DEST_EXISTS)

    def test_generate_refuses_the_raw_tree(self):
        loaded = catalog_check(root=REPO)
        with self.assertRaises(QbpRefusal) as raised:
            gen.generate(
                DEFAULT_RAW_OUTPUT_ROOT / "qbp-forbidden",
                catalog=loaded,
                mill_id="qbp-mill-leftover3-r42",
                rounds=(42,),
            )
        self.assertEqual(raised.exception.code, FINDING_GENERATE_RAW_TREE)


class QbpCliTests(unittest.TestCase):
    def test_catalog_check_cli(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.run(["catalog-check", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["pair_count"], N_PAIRS)
        self.assertEqual(payload["factory"], FACTORY)
        self.assertEqual(stderr.getvalue(), "")

    def test_generate_cli_one_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "cli-out"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = cli.run(
                    [
                        "generate",
                        "--out",
                        str(dest),
                        "--mill",
                        "qbp-mill-leftover3-r42",
                        "--round",
                        "42",
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["episodes"], 2)
            self.assertTrue((dest / "qbp-mill-leftover3-r42" / "batch-r42.jsonl").is_file())


if __name__ == "__main__":
    unittest.main()
