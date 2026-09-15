#!/usr/bin/env python3
"""CRP r538 slice: compact JSONL catalog, AST re-extract, generate gates."""

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

from crp import catalog as leftover3  # noqa: E402
from crp import cli, generate, r432, r538  # noqa: E402
from crp._contract import (  # noqa: E402
    FINDING_AST_NOT_A_PLANT,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_ROUND_OUT_OF_DOMAIN,
    CrpRefusal,
)
from record_kind import classify_kind  # noqa: E402


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogPins(unittest.TestCase):
    def test_committed_jsonl_is_compact_and_pinned(self):
        payload = (COMMITTED / "plants-r538.jsonl").read_bytes()
        text = payload.decode("utf-8")
        self.assertNotIn(b"\r", payload)
        self.assertTrue(text.endswith("\n"))
        lines = text.splitlines()
        self.assertEqual(len(lines), 495)
        self.assertTrue(all(line and line[:1] not in {" ", "\t"} for line in lines))
        digest = hashlib.sha256(payload).hexdigest()
        loaded = r538.load_catalog()
        report = r538.catalog_check()
        self.assertEqual(loaded.catalog_id, "crp-r538-v1")
        self.assertEqual(len(loaded.plants), 495)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], 495)
        self.assertEqual(report["triples"], 165)
        self.assertEqual(report["first_round"], 538)
        self.assertEqual(report["last_round"], 702)
        self.assertEqual(report["nouns"], 495)
        self.assertEqual(
            digest,
            json.loads((COMMITTED / "CATALOG-r538.json").read_text())["plants_sha256"],
        )
        self.assertEqual(loaded.plants[0].slug, "prefect-retries-zero-charge")
        self.assertEqual(loaded.plants[0].noun, "clew244")
        self.assertEqual(
            loaded.plants[0].repo,
            "plant/clew244-prefect-retries-zero-charge",
        )
        self.assertEqual(loaded.plants[-1].slug, "chicken-normalize-pathname-open-swap")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="crp-r538-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(COMMITTED, dest)
        meta_path = dest / "CATALOG-r538.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(CrpRefusal) as caught:
            r538.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_PLANTS_SHA_MISMATCH)

    def test_slugs_are_disjoint_from_leftover3_r432_and_prior(self):
        r538_slugs = {plant.slug for plant in r538.load_catalog().plants}
        leftover3_slugs = {plant.slug for plant in leftover3.load_catalog().plants}
        r432_slugs = {plant.slug for plant in r432.load_catalog().plants}
        self.assertFalse(r538_slugs & leftover3_slugs)
        self.assertFalse(r538_slugs & r432_slugs)
        proc = subprocess.run(
            ["git", "show", "origin/legacy-mill-lane:experiments/crp-mill-leftover3.py"],
            cwd=REPO,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            prior = leftover3.plants_from_source(proc.stdout.decode("utf-8"))
            self.assertFalse(r538_slugs & {plant.slug for plant in prior})


class AstExtract(unittest.TestCase):
    def test_committed_catalog_matches_legacy_ast(self):
        try:
            text = r538.git_show_source(r538.SOURCE_PATH)
        except CrpRefusal as exc:
            if exc.code == FINDING_AST_NOT_A_PLANT and "not fetchable" in str(exc):
                self.skipTest("legacy-mill-lane pin is not fetchable")
            raise
        extracted = leftover3.plants_from_source(text)
        committed = r538.load_catalog().plants
        self.assertEqual(len(extracted), 495)
        self.assertEqual(
            [(plant.slug, plant.noun, plant.family) for plant in extracted],
            [(plant.slug, plant.noun, plant.family) for plant in committed],
        )
        self.assertIn("Never", r538.git_show_source.__doc__ or "")
        self.assertEqual(r538.SOURCE_COMMIT, "813f93f1969c1c4421e5663492e9663739efa642")
        self.assertEqual(r538.SOURCE_SHA256, hashlib.sha256(text.encode("utf-8")).hexdigest())

    def test_wave_stops_before_r729_leftover3(self):
        self.assertLess(r538.WAVE_LAST_ROUND, leftover3.WAVE_FIRST_ROUND)

    def test_package_tree_has_no_vendored_mill_scripts(self):
        hits = list(PACKAGE.rglob("crp-mill*.py"))
        hits.extend(PACKAGE.rglob("crp-loop*.py"))
        hits.extend(PACKAGE.rglob("_gen_crp*.py"))
        hits.extend(COMMITTED.rglob("*mill*.py"))
        hits.extend(COMMITTED.rglob("*loop*.py"))
        self.assertEqual(hits, [])
        names = tuple(sorted(path.name for path in PACKAGE.glob("*.py")))
        self.assertEqual(
            names,
            (
                "__init__.py",
                "_contract.py",
                "catalog.py",
                "cli.py",
                "generate.py",
                "r432.py",
                "r538.py",
            ),
        )

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
        from pipelines.crp import r538 as packaged

        self.assertIs(packaged, r538)
        self.assertIs(sys.modules["crp.r538"], sys.modules["pipelines.crp.r538"])


class Generate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="crp-r538-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_round_554_writes_r538_triple_after_r432_wave(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest(554, out))
        self.assertEqual(summary["catalog_id"], "crp-r538-v1")
        self.assertEqual(summary["format"], "crp-r538-run/1")
        self.assertEqual(summary["records"], 3)
        plants = r538.plants_for_round(554)
        self.assertEqual(summary["nouns"], [plant.noun for plant in plants])
        first = json.loads((out / "batch-r554.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(first["id"], f"crp-r554-{plants[0].slug}")
        self.assertEqual(classify_kind(first), "preference")
        notes = (out / "NOTES-r554.md").read_text(encoding="utf-8")
        self.assertIn("r538 orchestration/data-platform stretch", notes)
        with self.assertRaises(CrpRefusal) as exists:
            generate.run(generate.RunRequest(554, out))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = self.root / "outputs" / "raw" / "x"
        with self.assertRaises(CrpRefusal) as under_raw:
            generate.run(generate.RunRequest(554, raw))
        self.assertEqual(under_raw.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())

    def test_round_538_still_routes_to_r432_when_both_waves_overlap(self):
        out = self.root / "r432-overlap"
        summary = generate.run(generate.RunRequest(538, out))
        self.assertEqual(summary["catalog_id"], "crp-r432-v1")

    def test_a_round_outside_the_r538_wave_is_refused_by_r538(self):
        with self.assertRaises(CrpRefusal) as ctx:
            r538.plants_for_round(703)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class Cli(unittest.TestCase):
    def test_catalog_check_r538_json_reports_nouns(self):
        code, out, err = invoke(["catalog-check", "--wave", "r538", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["catalog_id"], "crp-r538-v1")
        self.assertEqual(payload["plants"], 495)
        self.assertEqual(payload["nouns"], 495)


if __name__ == "__main__":
    unittest.main()
