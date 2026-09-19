#!/usr/bin/env python3
"""Contracts for the AST-extracted, non-executable leftover leftover leftover catalog."""

from __future__ import annotations

import ast
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from pipelines.lll import (
    CATALOG,
    FACTORY,
    FAMILY,
    GENERATOR,
    PREFIX,
    SOURCE_COMMIT,
    CatalogError,
    load_catalog,
)
from pipelines.mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "pipelines" / "lll"
CONFIG_DIR = ROOT / "config" / "lll"
CATALOG_JSON = CONFIG_DIR / "CATALOG.json"
PAIRS_JSONL = CONFIG_DIR / "pairs.jsonl"
PRESERVE = "813f93f1969c1c4421e5663492e9663739efa642"

SOURCE_PROVENANCE = {
    "experiments/mill_leftover_leftover_leftover_r56.py": (
        56,
        16,
        758,
        "e0096debbc417c648cd41b078dc62b8277e5104d",
        "38a1304441ecb930579fe3e3fc065e704c3f18db746170c103c3965769f84fb5",
        "pm-serverid-bind",
        "fb-msgid-bind",
    ),
    "experiments/mill_leftover_leftover_leftover_r59.py": (
        59,
        16,
        776,
        "84e0143cdfc64c31da21e6cb14863f385f277c0a",
        "d112d255a1053f8a69fcc6247e029b45d894fe6831ca875867a2203e768129a9",
        "loops-contactid-bind",
        "rs-broadcast-bind",
    ),
    "experiments/mill_leftover_leftover_leftover_r75.py": (
        75,
        16,
        776,
        "9165f46a9328706867749a59ea3b4158deb9645d",
        "946a1180d1d90690b60844bab4d6a176f45f53759085da7eddf8b78ff7d46d47",
        "loops-mailingid-bind",
        "rs-template-bind",
    ),
    "experiments/mill_leftover_leftover_leftover_r91.py": (
        91,
        16,
        781,
        "745303a780bb1cb90c747952edce0b12a6420a55",
        "f81136f578a3ff1384e9fa7cf058afe24b416203ade1c22475920e3fc99d7a4c",
        "sg-asm-group-bind",
        "drip-broadcast-bind",
    ),
}


def _literal(node: ast.AST) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_literal(elt) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_literal(elt) for elt in node.elts)
    if isinstance(node, ast.Dict):
        return {_literal(key): _literal(value) for key, value in zip(node.keys, node.values)}
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "dict":
            return {keyword.arg: _literal(keyword.value) for keyword in node.keywords}
        if isinstance(node.func, ast.Attribute) and node.func.attr == "replace":
            target = _literal(node.func.value)
            args = [_literal(argument) for argument in node.args]
            return target.replace(*args)
        raise ValueError(f"non-literal Call {ast.dump(node.func)}")
    raise ValueError(type(node).__name__)


def _ast_pairs(source: str) -> list[dict[str, object]]:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if "PAIRS" in names:
            pairs = _literal(node.value)
            if not isinstance(pairs, list):
                raise TypeError("PAIRS is not a list")
            return pairs
    raise KeyError("PAIRS")


def _legacy_source(relpath: str) -> str | None:
    for spec in (f"{PRESERVE}:{relpath}", f"origin/legacy-mill-lane:{relpath}"):
        try:
            return subprocess.check_output(["git", "show", spec], text=True, cwd=ROOT)
        except subprocess.CalledProcessError:
            continue
    return None


class LllCatalogTests(unittest.TestCase):
    def test_catalog_preserves_all_ast_extracted_case_counts(self):
        pairs = list(CATALOG.pairs())
        record_ids = list(CATALOG.record_ids())

        self.assertEqual(len(CATALOG.catalogs), 4)
        self.assertEqual(len(pairs), 64)
        self.assertEqual(len(record_ids), 128)
        self.assertEqual(len(record_ids), len(set(record_ids)))
        self.assertEqual(sum(source.source_lines for source in CATALOG.catalogs), 3091)

    def test_source_ranges_and_hashes_pin_the_legacy_ast_inputs(self):
        observed = {
            source.source_path: (
                source.catalog_first,
                source.pair_count,
                source.source_lines,
                source.source_blob_sha1,
                source.source_sha256,
                source.first_slug,
                source.last_slug,
            )
            for source in CATALOG.catalogs
        }
        self.assertEqual(observed, SOURCE_PROVENANCE)
        self.assertEqual(CATALOG.source_commit, SOURCE_COMMIT)
        self.assertEqual(CATALOG.source_commit, PRESERVE)
        self.assertEqual(CATALOG.family, FAMILY)
        self.assertEqual(CATALOG.factory, FACTORY)
        self.assertEqual(CATALOG.prefix, PREFIX)
        self.assertEqual(CATALOG.generator, GENERATOR)
        self.assertIn("never imported or executed", CATALOG.extraction)

    def test_reviewed_ewr_prefix_home_is_unchanged(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[PREFIX], FACTORY)
        self.assertNotIn(FAMILY, REVIEWED_MILL_PREFIX_HOMES)

    def test_identity_is_mill_and_index_not_unique_rounds(self):
        rounds = [pair.round for pair in CATALOG.pairs()]
        identities = [(pair.mill_id, pair.index) for pair in CATALOG.pairs()]
        mill_slugs = [(pair.mill_id, pair.success.slug) for pair in CATALOG.pairs()]
        self.assertEqual(len(identities), 64)
        self.assertEqual(len(identities), len(set(identities)))
        self.assertEqual(len(mill_slugs), len(set(mill_slugs)))
        self.assertLess(len(set(rounds)), 64)
        self.assertTrue({56, 59, 71, 74, 75, 90, 91, 106}.issubset(set(rounds)))

    def test_each_pair_has_one_success_and_one_handoff_case(self):
        for pair in CATALOG.pairs():
            self.assertNotEqual(pair.success.slug, pair.handoff.slug)
            self.assertNotEqual(pair.success.mod, pair.handoff.mod)
            self.assertTrue(pair.success.docs[0].startswith("https://"))
            self.assertTrue(pair.handoff.docs[1].startswith("https://"))
            self.assertEqual(pair.round, pair.catalog_first + pair.index)
            blob = " ".join(
                (
                    pair.success.slug,
                    pair.handoff.slug,
                    pair.success.domain,
                    pair.handoff.ticket,
                )
            ).lower()
            self.assertNotIn("beehiiv", blob)
            self.assertNotIn("constant-contact", blob)
            self.assertNotIn("sir-", blob)

    def test_legacy_mills_are_not_vendored_or_executable(self):
        package_files = {path.name for path in PACKAGE.iterdir() if path.is_file()}
        self.assertEqual(package_files, {"__init__.py", "catalog.py"})
        self.assertEqual(list(PACKAGE.glob("mill_leftover_leftover_leftover_*.py")), [])

        forbidden_functions = {"main", "run_loop", "emit_stage", "publish_round"}
        for path in PACKAGE.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            functions = {
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            imports = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names
            }
            names = {
                node.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Name)
            }
            self.assertTrue(functions.isdisjoint(forbidden_functions))
            self.assertNotIn("subprocess", imports)
            self.assertNotIn("round_txn", imports)
            self.assertTrue(names.isdisjoint({"exec", "eval", "compile"}))
            self.assertNotIn("outputs/raw", source)

    def test_pairs_jsonl_stays_compact(self):
        text = PAIRS_JSONL.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), 64)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            json.loads(line)

    def test_loader_fails_closed_on_a_missing_case_field(self):
        header = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        lines = PAIRS_JSONL.read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        del first["success"]["idf"]
        lines[0] = json.dumps(first, separators=(",", ":"))

        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            (dest / "pairs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(CatalogError, "keys differ"):
                load_catalog(dest)

    def test_ast_reextract_matches_committed_slugs_when_archive_exists(self):
        extracted = 0
        for source in CATALOG.catalogs:
            text = _legacy_source(source.source_path)
            if text is None:
                continue
            pairs = _ast_pairs(text)
            self.assertEqual(len(pairs), source.pair_count)
            self.assertEqual(pairs[0]["slug"], source.first_slug)
            self.assertEqual(pairs[-1]["slug"], source.last_slug)
            self.assertEqual(
                [row["slug"] for row in pairs],
                [pair.success.slug for pair in source.pairs],
            )
            self.assertEqual(
                [row["fail"] for row in pairs],
                [pair.handoff.slug for pair in source.pairs],
            )
            extracted += 1
        if extracted == 0:
            self.skipTest("preserve archive blobs are not present in this checkout")
        self.assertEqual(extracted, 4)


if __name__ == "__main__":
    unittest.main()
