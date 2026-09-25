#!/usr/bin/env python3
"""CRP r817 slice: ``crp-mill-r817`` compact JSONL catalog."""

from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
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
from crp import cli, generate, leftover3_prior, r432, r538, r729, r817  # noqa: E402
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
    "wave_catalog.py",
)


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogPins(unittest.TestCase):
    def test_committed_jsonl_is_compact_and_pinned(self):
        payload = (COMMITTED / "plants-r817.jsonl").read_bytes()
        text = payload.decode("utf-8")
        self.assertNotIn(b"\r", payload)
        self.assertTrue(text.endswith("\n"))
        lines = text.splitlines()
        self.assertEqual(len(lines), 534)
        digest = hashlib.sha256(payload).hexdigest()
        loaded = r817.load_catalog()
        report = r817.catalog_check()
        self.assertEqual(loaded.catalog_id, "crp-r817-v1")
        self.assertEqual(report["plants"], 534)
        self.assertEqual(report["triples"], 178)
        self.assertEqual(report["first_round"], 817)
        self.assertEqual(report["last_round"], 994)
        self.assertEqual(
            digest,
            json.loads((COMMITTED / "CATALOG-r817.json").read_text())["plants_sha256"],
        )
        self.assertEqual(loaded.plants[0].slug, "postgis-exclude-overlap-parcel")
        self.assertEqual(loaded.plants[0].noun, "atoll900")
        self.assertEqual(loaded.plants[-1].slug, "dashy-section-name-case")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="crp-r817-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(COMMITTED, dest)
        meta_path = dest / "CATALOG-r817.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(CrpRefusal) as caught:
            r817.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_PLANTS_SHA_MISMATCH)

    def test_slugs_are_disjoint_from_other_crp_waves(self):
        r817_slugs = {plant.slug for plant in r817.load_catalog().plants}
        for other in (
            cat.load_catalog().plants,
            leftover3_prior.load_catalog().plants,
            r432.load_catalog().plants,
            r538.load_catalog().plants,
            r729.load_catalog().plants,
        ):
            self.assertFalse(r817_slugs & {plant.slug for plant in other})


class AstExtract(unittest.TestCase):
    def test_committed_catalog_matches_legacy_ast(self):
        try:
            text = r817.git_show_source(r817.SOURCE_PATH)
        except CrpRefusal as exc:
            if exc.code == FINDING_AST_NOT_A_PLANT and "not fetchable" in str(exc):
                self.skipTest("legacy-mill-lane pin is not fetchable")
            raise
        extracted = cat.plants_from_source(text)
        committed = r817.load_catalog().plants
        self.assertEqual(len(extracted), 534)
        self.assertEqual(
            [(plant.slug, plant.noun, plant.family) for plant in extracted],
            [(plant.slug, plant.noun, plant.family) for plant in committed],
        )

    def test_r817_starts_after_r729_wave(self):
        self.assertGreater(r817.WAVE_FIRST_ROUND, r729.WAVE_LAST_ROUND)

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
        self.root = Path(tempfile.mkdtemp(prefix="crp-r817-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_round_817_writes_r817_triple(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest(817, out))
        self.assertEqual(summary["catalog_id"], "crp-r817-v1")
        self.assertEqual(summary["format"], "crp-r817-run/1")
        plants = r817.plants_for_round(817)
        first = json.loads((out / "batch-r817.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(first["id"], f"crp-r817-{plants[0].slug}")
        self.assertEqual(classify_kind(first), "preference")
        notes = (out / "NOTES-r817.md").read_text(encoding="utf-8")
        self.assertIn("r817 GIS", notes)
        with self.assertRaises(CrpRefusal) as exists:
            generate.run(generate.RunRequest(817, out))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = self.root / "outputs" / "raw" / "x"
        with self.assertRaises(CrpRefusal) as under_raw:
            generate.run(generate.RunRequest(817, raw))
        self.assertEqual(under_raw.exception.code, FINDING_DESTINATION_UNDER_RAW)

    def test_round_800_still_routes_to_r729(self):
        out = self.root / "r729"
        summary = generate.run(generate.RunRequest(800, out))
        self.assertEqual(summary["catalog_id"], "crp-r729-v1")

    def test_out_of_domain_r817_round_is_refused(self):
        with self.assertRaises(CrpRefusal) as ctx:
            r817.plants_for_round(995)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class Cli(unittest.TestCase):
    def test_catalog_check_r817_json(self):
        code, out, err = invoke(["catalog-check", "--wave", "r817", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["catalog_id"], "crp-r817-v1")
        self.assertEqual(payload["plants"], 534)


if __name__ == "__main__":
    unittest.main()
