#!/usr/bin/env python3
"""CRP r995 slice: ``crp-mill-r995`` compact JSONL catalog prefix."""

from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
COMMITTED = REPO / "config" / "crp"
PACKAGE = PIPELINES / "crp"
sys.path.insert(0, str(PIPELINES))

from crp import catalog as cat  # noqa: E402
from crp import cli, generate, leftover3_prior, r432, r538, r729, r817, r995  # noqa: E402
from crp._contract import (  # noqa: E402
    FINDING_AST_NOT_A_PLANT,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_ROUND_OUT_OF_DOMAIN,
    CrpRefusal,
)
from record_kind import classify_kind  # noqa: E402

PACKAGE_PY = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "cli.py",
    "generate.py",
    "leftover3_prior.py",
    "r432.py",
    "r538.py",
    "r729.py",
    "r817.py",
    "r995.py",
)
MILL_PLANTS = 1968
PREFIX_PLANTS = 1728
PREFIX_TRIPLES = PREFIX_PLANTS // 3


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogPins(unittest.TestCase):
    def test_committed_jsonl_is_compact_and_pinned(self):
        payload = (COMMITTED / "plants-r995.jsonl").read_bytes()
        text = payload.decode("utf-8")
        self.assertNotIn(b"\r", payload)
        self.assertTrue(text.endswith("\n"))
        lines = text.splitlines()
        self.assertEqual(len(lines), PREFIX_PLANTS)
        digest = hashlib.sha256(payload).hexdigest()
        loaded = r995.load_catalog()
        report = r995.catalog_check()
        self.assertEqual(loaded.catalog_id, "crp-r995-v1")
        self.assertEqual(report["plants"], PREFIX_PLANTS)
        self.assertEqual(report["triples"], PREFIX_TRIPLES)
        self.assertEqual(report["first_round"], 995)
        self.assertEqual(report["last_round"], 1570)
        meta = json.loads((COMMITTED / "CATALOG-r995.json").read_text())
        self.assertEqual(digest, meta["plants_sha256"])
        self.assertEqual(meta["slice"], "prefix")
        self.assertEqual(loaded.plants[0].slug, "nocobase-collection-name-case")
        self.assertEqual(loaded.plants[0].noun, "reef1000")
        self.assertEqual(loaded.plants[-1].slug, "cfenginex3-name-case")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="crp-r995-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(COMMITTED, dest)
        meta_path = dest / "CATALOG-r995.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(CrpRefusal) as caught:
            r995.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_PLANTS_SHA_MISMATCH)

    def test_slugs_are_disjoint_from_other_crp_waves(self):
        r995_slugs = {plant.slug for plant in r995.load_catalog().plants}
        for other in (
            cat.load_catalog().plants,
            leftover3_prior.load_catalog().plants,
            r432.load_catalog().plants,
            r538.load_catalog().plants,
            r729.load_catalog().plants,
            r817.load_catalog().plants,
        ):
            self.assertFalse(r995_slugs & {plant.slug for plant in other})


class AstExtract(unittest.TestCase):
    def test_committed_catalog_matches_legacy_ast(self):
        try:
            text = r995.git_show_source(r995.SOURCE_PATH)
        except CrpRefusal as exc:
            if exc.code == FINDING_AST_NOT_A_PLANT and "not fetchable" in str(exc):
                self.skipTest("legacy-mill-lane pin is not fetchable")
            raise
        extracted = cat.plants_from_source(text)
        committed = r995.load_catalog().plants
        self.assertEqual(len(extracted), MILL_PLANTS)
        self.assertEqual(len(committed), PREFIX_PLANTS)
        self.assertEqual(
            [(plant.slug, plant.noun, plant.family) for plant in extracted[:len(committed)]],
            [(plant.slug, plant.noun, plant.family) for plant in committed],
        )

    def test_r995_starts_after_r817_wave(self):
        self.assertGreater(r995.WAVE_FIRST_ROUND, r817.WAVE_LAST_ROUND)

    def test_package_tree_has_no_vendored_mill_scripts(self):
        self.assertEqual(list(PACKAGE.rglob("crp-mill*.py")), [])
        names = tuple(sorted(path.name for path in PACKAGE.glob("*.py")))
        self.assertEqual(names, PACKAGE_PY)

    def test_package_has_no_exec_eval_compile(self):
        for path in PACKAGE.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            calls = [
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            ]
            self.assertNotIn("exec", calls, path.name)
            self.assertNotIn("eval", calls, path.name)
            self.assertNotIn("compile", calls, path.name)


class Generate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="crp-r995-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_round_995_writes_r995_triple(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest(995, out))
        self.assertEqual(summary["catalog_id"], "crp-r995-v1")
        self.assertEqual(summary["format"], "crp-r995-run/1")
        plants = r995.plants_for_round(995)
        first = json.loads((out / "batch-r995.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(first["id"], f"crp-r995-{plants[0].slug}")
        self.assertEqual(classify_kind(first), "preference")
        notes = (out / "NOTES-r995.md").read_text(encoding="utf-8")
        self.assertIn("r995 low-code", notes)
        with self.assertRaises(CrpRefusal) as exists:
            generate.run(generate.RunRequest(995, out))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = self.root / "outputs" / "raw" / "x"
        with self.assertRaises(CrpRefusal) as under_raw:
            generate.run(generate.RunRequest(995, raw))
        self.assertEqual(under_raw.exception.code, FINDING_DESTINATION_UNDER_RAW)

    def test_round_994_still_routes_to_r817(self):
        out = self.root / "r817"
        summary = generate.run(generate.RunRequest(994, out))
        self.assertEqual(summary["catalog_id"], "crp-r817-v1")

    def test_out_of_domain_r995_round_is_refused(self):
        with self.assertRaises(CrpRefusal) as ctx:
            r995.plants_for_round(1571)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class Cli(unittest.TestCase):
    def test_catalog_check_r995_json(self):
        code, out, err = invoke(["catalog-check", "--wave", "r995", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["catalog_id"], "crp-r995-v1")
        self.assertEqual(payload["plants"], PREFIX_PLANTS)


if __name__ == "__main__":
    unittest.main()
