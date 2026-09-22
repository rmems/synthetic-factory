#!/usr/bin/env python3
"""CRP r729 slice: compact JSONL catalog, AST re-extract, generate gates."""

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
sys.path.insert(0, str(Path(__file__).resolve().parent))

from crp import catalog as leftover3  # noqa: E402
from crp import cli, generate, r432, r538, r729  # noqa: E402
from crp._contract import (  # noqa: E402
    FINDING_AST_NOT_A_PLANT,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_ROUND_OUT_OF_DOMAIN,
    CrpRefusal,
)
from record_kind import classify_kind  # noqa: E402
from crp_test_support import PACKAGE_PY, package_py_names, vendored_mill_script_hits  # noqa: E402


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogPins(unittest.TestCase):
    def test_committed_jsonl_is_compact_and_pinned(self):
        payload = (COMMITTED / "plants-r729.jsonl").read_bytes()
        text = payload.decode("utf-8")
        self.assertNotIn(b"\r", payload)
        self.assertTrue(text.endswith("\n"))
        lines = text.splitlines()
        self.assertEqual(len(lines), 216)
        self.assertTrue(all(line and line[:1] not in {" ", "\t"} for line in lines))
        digest = hashlib.sha256(payload).hexdigest()
        loaded = r729.load_catalog()
        report = r729.catalog_check()
        self.assertEqual(loaded.catalog_id, "crp-r729-v1")
        self.assertEqual(len(loaded.plants), 216)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], 216)
        self.assertEqual(report["triples"], 72)
        self.assertEqual(report["first_round"], 729)
        self.assertEqual(report["last_round"], 800)
        self.assertEqual(report["nouns"], 216)
        self.assertEqual(
            digest,
            json.loads((COMMITTED / "CATALOG-r729.json").read_text())["plants_sha256"],
        )
        self.assertEqual(loaded.plants[0].slug, "magento-quote-collect-unlocked")
        self.assertEqual(loaded.plants[0].noun, "keel800")
        self.assertEqual(
            loaded.plants[0].repo,
            "plant/keel800-magento-quote-collect-unlocked",
        )
        self.assertEqual(loaded.plants[-1].slug, "mlserver-stream-replay")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="crp-r729-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(COMMITTED, dest)
        meta_path = dest / "CATALOG-r729.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(CrpRefusal) as caught:
            r729.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_PLANTS_SHA_MISMATCH)

    def test_slugs_are_disjoint_from_leftover3_r432_r538_and_prior(self):
        r729_slugs = {plant.slug for plant in r729.load_catalog().plants}
        leftover3_slugs = {plant.slug for plant in leftover3.load_catalog().plants}
        r432_slugs = {plant.slug for plant in r432.load_catalog().plants}
        r538_slugs = {plant.slug for plant in r538.load_catalog().plants}
        self.assertFalse(r729_slugs & leftover3_slugs)
        self.assertFalse(r729_slugs & r432_slugs)
        self.assertFalse(r729_slugs & r538_slugs)
        proc = subprocess.run(
            ["git", "show", "origin/legacy-mill-lane:experiments/crp-mill-leftover3.py"],
            cwd=REPO,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            prior = leftover3.plants_from_source(proc.stdout.decode("utf-8"))
            self.assertFalse(r729_slugs & {plant.slug for plant in prior})


class AstExtract(unittest.TestCase):
    def test_committed_catalog_matches_legacy_ast(self):
        try:
            text = r729.git_show_source(r729.SOURCE_PATH)
        except CrpRefusal as exc:
            if exc.code == FINDING_AST_NOT_A_PLANT and "not fetchable" in str(exc):
                self.skipTest("legacy-mill-lane pin is not fetchable")
            raise
        extracted = leftover3.plants_from_source(text)
        committed = r729.load_catalog().plants
        self.assertEqual(len(extracted), 216)
        self.assertEqual(
            [(plant.slug, plant.noun, plant.family) for plant in extracted],
            [(plant.slug, plant.noun, plant.family) for plant in committed],
        )
        self.assertIn("Never", r729.git_show_source.__doc__ or "")
        self.assertEqual(r729.SOURCE_COMMIT, "813f93f1969c1c4421e5663492e9663739efa642")
        self.assertEqual(r729.SOURCE_SHA256, hashlib.sha256(text.encode("utf-8")).hexdigest())

    def test_generate_prefers_leftover3_for_rounds_shared_with_r729_catalog(self):
        leftover3_last = leftover3.WAVE_FIRST_ROUND + len(leftover3.load_catalog().plants) // 3 - 1
        self.assertEqual(leftover3_last, 744)
        self.assertEqual(r729.WAVE_FIRST_ROUND, leftover3.WAVE_FIRST_ROUND)
        self.assertGreater(r729.WAVE_LAST_ROUND, leftover3_last)

    def test_package_tree_has_no_vendored_mill_scripts(self):
        self.assertEqual(vendored_mill_script_hits(), [])
        self.assertEqual(package_py_names(), PACKAGE_PY)

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

    def test_both_import_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.crp import r729 as packaged

        self.assertIs(packaged, r729)
        self.assertIs(sys.modules["crp.r729"], sys.modules["pipelines.crp.r729"])


class Generate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="crp-r729-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_round_745_writes_r729_triple_after_leftover3_wave(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest(745, out))
        self.assertEqual(summary["catalog_id"], "crp-r729-v1")
        self.assertEqual(summary["format"], "crp-r729-run/1")
        self.assertEqual(summary["records"], 3)
        plants = r729.plants_for_round(745)
        self.assertEqual(summary["nouns"], [plant.noun for plant in plants])
        first = json.loads((out / "batch-r745.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(first["id"], f"crp-r745-{plants[0].slug}")
        self.assertEqual(classify_kind(first), "preference")
        notes = (out / "NOTES-r745.md").read_text(encoding="utf-8")
        self.assertIn("r729 commerce/platform stretch", notes)
        with self.assertRaises(CrpRefusal) as exists:
            generate.run(generate.RunRequest(745, out))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = self.root / "outputs" / "raw" / "x"
        with self.assertRaises(CrpRefusal) as under_raw:
            generate.run(generate.RunRequest(745, raw))
        self.assertEqual(under_raw.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())

    def test_round_729_still_routes_to_leftover3_when_both_waves_overlap(self):
        out = self.root / "leftover3-overlap"
        summary = generate.run(generate.RunRequest(729, out))
        self.assertEqual(summary["catalog_id"], "crp-leftover3-v1")
        self.assertEqual(summary["slugs"][0], "terraform-target-orphan-sku")

    def test_a_round_outside_the_r729_wave_is_refused_by_r729(self):
        with self.assertRaises(CrpRefusal) as ctx:
            r729.plants_for_round(801)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class Cli(unittest.TestCase):
    def test_catalog_check_r729_json_reports_nouns(self):
        code, out, err = invoke(["catalog-check", "--wave", "r729", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["catalog_id"], "crp-r729-v1")
        self.assertEqual(payload["plants"], 216)
        self.assertEqual(payload["nouns"], 216)


if __name__ == "__main__":
    unittest.main()
