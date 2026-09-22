#!/usr/bin/env python3
"""CRP r432 slice: compact JSONL catalog, AST re-extract, generate gates."""

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
from unittest import mock

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
from mill_family import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from record_kind import classify_kind  # noqa: E402


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogPins(unittest.TestCase):
    def test_patched_default_directory_is_live_and_isolated_per_wave(self):
        root = Path(tempfile.mkdtemp(prefix="crp-r432-default-"))
        self.addCleanup(shutil.rmtree, root, True)
        shutil.copytree(COMMITTED, root / "catalog")
        r538_default = r538.default_catalog_dir()

        with mock.patch.object(r432, "DEFAULT_CATALOG_DIR", root / "catalog"):
            self.assertEqual(len(r432.load_catalog().plants), r432.EXPECTED_PLANTS)
            self.assertEqual(r538.default_catalog_dir(), r538_default)
            self.assertNotEqual(r432.default_catalog_dir(), r538.default_catalog_dir())

    def test_committed_jsonl_is_compact_and_pinned(self):
        payload = (COMMITTED / "plants.jsonl").read_bytes()
        text = payload.decode("utf-8")
        self.assertNotIn(b"\r", payload)
        self.assertTrue(text.endswith("\n"))
        lines = text.splitlines()
        self.assertEqual(len(lines), 366)
        self.assertTrue(all(line and line[:1] not in {" ", "\t"} for line in lines))
        digest = hashlib.sha256(payload).hexdigest()
        loaded = r432.load_catalog()
        report = r432.catalog_check()
        self.assertEqual(loaded.catalog_id, "crp-r432-v1")
        self.assertEqual(len(loaded.plants), 366)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], 366)
        self.assertEqual(report["triples"], 122)
        self.assertEqual(report["first_round"], 432)
        self.assertEqual(report["last_round"], 553)
        self.assertEqual(report["nouns"], 366)
        self.assertEqual(digest, json.loads((COMMITTED / "CATALOG.json").read_text())["plants_sha256"])
        self.assertEqual(loaded.plants[0].slug, "django-f-inventory-oversell")
        self.assertEqual(loaded.plants[0].noun, "quay")
        self.assertEqual(loaded.plants[0].repo, "plant/quay-django-f-inventory-oversell")
        self.assertEqual(loaded.plants[-1].slug, "iceberg-rewrite-lost-snapshot")
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES["crp"], leftover3.FACTORY)

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="crp-r432-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(COMMITTED, dest)
        meta_path = dest / "CATALOG.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(CrpRefusal) as caught:
            r432.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_PLANTS_SHA_MISMATCH)

    def test_slugs_are_disjoint_from_leftover3_and_prior(self):
        r432_slugs = {plant.slug for plant in r432.load_catalog().plants}
        leftover3_slugs = {plant.slug for plant in leftover3.load_catalog().plants}
        self.assertFalse(r432_slugs & leftover3_slugs)
        # #307 leftover3-prior wave (r679); first and last committed slugs.
        self.assertNotIn("terraform-statelock-skip-apply", r432_slugs)
        self.assertNotIn("fx-invoke-onstart-double-hook", r432_slugs)


class AstExtract(unittest.TestCase):
    def test_committed_catalog_matches_legacy_ast(self):
        try:
            text = r432.git_show_source(r432.SOURCE_PATH)
        except CrpRefusal as exc:
            if exc.code == FINDING_AST_NOT_A_PLANT and "not fetchable" in str(exc):
                self.skipTest("legacy-mill-lane pin is not fetchable")
            raise
        extracted = leftover3.plants_from_source(text)
        committed = r432.load_catalog().plants
        self.assertEqual(len(extracted), 366)
        self.assertEqual(
            [(plant.slug, plant.noun, plant.family) for plant in extracted],
            [(plant.slug, plant.noun, plant.family) for plant in committed],
        )
        self.assertIn("Never", r432.git_show_source.__doc__ or "")
        self.assertEqual(r432.SOURCE_COMMIT, "9237367ce58fb8d472e5fbc18e5dbffff35bca76")
        self.assertEqual(r432.SOURCE_SHA256, hashlib.sha256(text.encode("utf-8")).hexdigest())

    def test_prior_leftover3_mill_stays_disjoint_when_present(self):
        proc = subprocess.run(
            ["git", "show", "origin/legacy-mill-lane:experiments/crp-mill-leftover3.py"],
            cwd=REPO,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            self.skipTest("leftover3-prior mill is not fetchable")
        prior = leftover3.plants_from_source(proc.stdout.decode("utf-8"))
        r432_slugs = {plant.slug for plant in r432.load_catalog().plants}
        self.assertEqual(len(prior), 48)
        self.assertFalse(r432_slugs & {plant.slug for plant in prior})

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
                "leftover3_prior.py",
                "r432.py",
                "r538.py",
                "r729.py",
                "r817.py",
                "r995.py",
                "wave_catalog.py",
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
        from pipelines.crp import r432 as packaged

        self.assertIs(packaged, r432)
        self.assertIs(sys.modules["crp.r432"], sys.modules["pipelines.crp.r432"])


class Generate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="crp-r432-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_round_432_writes_three_records_and_refuses_clobber_or_raw(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest(432, out))
        self.assertEqual(summary["catalog_id"], "crp-r432-v1")
        self.assertEqual(summary["format"], "crp-r432-run/1")
        self.assertEqual(summary["records"], 3)
        self.assertEqual(summary["nouns"], ["quay", "slip", "berth"])
        self.assertEqual(summary["slugs"][0], "django-f-inventory-oversell")
        first = json.loads((out / "batch-r432.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(first["id"], "crp-r432-django-f-inventory-oversell")
        self.assertEqual(classify_kind(first), "preference")
        self.assertEqual(first["meta"]["noun"], "quay")
        notes = (out / "NOTES-r432.md").read_text(encoding="utf-8")
        self.assertIn("r432 application-bug stretch", notes)
        self.assertIn("noun=`quay`", notes)
        with self.assertRaises(CrpRefusal) as exists:
            generate.run(generate.RunRequest(432, out))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = self.root / "outputs" / "raw" / "x"
        with self.assertRaises(CrpRefusal) as under_raw:
            generate.run(generate.RunRequest(432, raw))
        self.assertEqual(under_raw.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())

    def test_a_round_outside_the_r432_wave_is_refused_by_r432(self):
        with self.assertRaises(CrpRefusal) as ctx:
            r432.plants_for_round(431)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)
        with self.assertRaises(CrpRefusal) as leftover:
            leftover3.plants_for_round(432)
        self.assertEqual(leftover.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class Cli(unittest.TestCase):
    def test_catalog_check_r432_json_reports_nouns(self):
        code, out, err = invoke(["catalog-check", "--wave", "r432", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["catalog_id"], "crp-r432-v1")
        self.assertEqual(payload["plants"], 366)
        self.assertEqual(payload["nouns"], 366)

    def test_default_catalog_check_stays_leftover3(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["catalog_id"], "crp-leftover3-v1")
        self.assertEqual(payload["plants"], 48)


if __name__ == "__main__":
    unittest.main()
