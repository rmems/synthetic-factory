#!/usr/bin/env python3
"""CRP leftover3-prior slice: ``crp-mill-leftover3`` compact JSONL catalog."""

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
from crp import cli, generate, leftover3_prior, r432, r538, r729  # noqa: E402
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


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogPins(unittest.TestCase):
    def test_committed_jsonl_is_compact_and_pinned(self):
        payload = (COMMITTED / "plants-leftover3-prior.jsonl").read_bytes()
        text = payload.decode("utf-8")
        self.assertNotIn(b"\r", payload)
        self.assertTrue(text.endswith("\n"))
        lines = text.splitlines()
        self.assertEqual(len(lines), 48)
        self.assertTrue(all(line and line[:1] not in {" ", "\t"} for line in lines))
        digest = hashlib.sha256(payload).hexdigest()
        loaded = leftover3_prior.load_catalog()
        report = leftover3_prior.catalog_check()
        self.assertEqual(loaded.catalog_id, "crp-leftover3-prior-v1")
        self.assertEqual(len(loaded.plants), 48)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["triples"], 16)
        self.assertEqual(report["first_round"], 679)
        self.assertEqual(report["last_round"], 694)
        self.assertEqual(
            digest,
            json.loads((COMMITTED / "CATALOG-leftover3-prior.json").read_text())[
                "plants_sha256"
            ],
        )
        self.assertEqual(loaded.plants[0].slug, "terraform-statelock-skip-apply")
        self.assertEqual(loaded.plants[0].noun, "keel701")
        self.assertEqual(loaded.plants[-1].slug, "fx-invoke-onstart-double-hook")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="crp-l3prior-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(COMMITTED, dest)
        meta_path = dest / "CATALOG-leftover3-prior.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(CrpRefusal) as caught:
            leftover3_prior.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_PLANTS_SHA_MISMATCH)

    def test_slugs_are_disjoint_from_other_crp_waves(self):
        prior_slugs = {plant.slug for plant in leftover3_prior.load_catalog().plants}
        for other in (
            cat.load_catalog().plants,
            r432.load_catalog().plants,
            r538.load_catalog().plants,
            r729.load_catalog().plants,
        ):
            self.assertFalse(prior_slugs & {plant.slug for plant in other})


class AstExtract(unittest.TestCase):
    def test_committed_catalog_matches_legacy_ast(self):
        try:
            text = leftover3_prior.git_show_source(leftover3_prior.SOURCE_PATH)
        except CrpRefusal as exc:
            if exc.code == FINDING_AST_NOT_A_PLANT and "not fetchable" in str(exc):
                self.skipTest("legacy-mill-lane pin is not fetchable")
            raise
        extracted = cat.plants_from_source(text)
        committed = leftover3_prior.load_catalog().plants
        self.assertEqual(len(extracted), 48)
        self.assertEqual(
            [(plant.slug, plant.noun, plant.family) for plant in extracted],
            [(plant.slug, plant.noun, plant.family) for plant in committed],
        )
        self.assertEqual(
            leftover3_prior.SOURCE_SHA256,
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )

    def test_prior_wave_overlaps_r538_but_routes_first(self):
        self.assertLessEqual(leftover3_prior.WAVE_FIRST_ROUND, r538.WAVE_LAST_ROUND)
        self.assertGreaterEqual(leftover3_prior.WAVE_LAST_ROUND, r538.WAVE_FIRST_ROUND)

    def test_package_tree_has_no_vendored_mill_scripts(self):
        hits = list(PACKAGE.rglob("crp-mill*.py"))
        hits.extend(PACKAGE.rglob("crp-loop*.py"))
        hits.extend(PACKAGE.rglob("_gen_crp*.py"))
        self.assertEqual(hits, [])
        names = tuple(sorted(path.name for path in PACKAGE.glob("*.py")))
        self.assertEqual(names, PACKAGE_PY)

    def test_both_import_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.crp import leftover3_prior as packaged

        self.assertIs(packaged, leftover3_prior)


class Generate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="crp-l3prior-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_round_679_writes_prior_triple_over_r538_overlap(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest(679, out))
        self.assertEqual(summary["catalog_id"], "crp-leftover3-prior-v1")
        self.assertEqual(summary["format"], "crp-leftover3-prior-run/1")
        plants = leftover3_prior.plants_for_round(679)
        self.assertEqual(summary["slugs"][0], plants[0].slug)
        first = json.loads((out / "batch-r679.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(classify_kind(first), "preference")
        notes = (out / "NOTES-r679.md").read_text(encoding="utf-8")
        self.assertIn("prior wave", notes)

    def test_round_695_falls_through_to_r538(self):
        out = self.root / "r538"
        summary = generate.run(generate.RunRequest(695, out))
        self.assertEqual(summary["catalog_id"], "crp-r538-v1")

    def test_out_of_domain_prior_round_is_refused(self):
        with self.assertRaises(CrpRefusal) as ctx:
            leftover3_prior.plants_for_round(678)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class Cli(unittest.TestCase):
    def test_catalog_check_prior_json(self):
        code, out, err = invoke(["catalog-check", "--wave", "leftover3-prior", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["catalog_id"], "crp-leftover3-prior-v1")
        self.assertEqual(payload["plants"], 48)


if __name__ == "__main__":
    unittest.main()
