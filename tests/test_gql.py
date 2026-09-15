#!/usr/bin/env python3
"""GQL mill package: catalog pins, AST extract, generate, CLI, no vendored mills."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURE = REPO / "tests" / "fixtures" / "gql"
COMMITTED = REPO / "config" / "gql"

sys.path.insert(0, str(PIPELINES))

from gql import catalog, cli, generate  # noqa: E402
from gql._contract import (  # noqa: E402
    FACTORY,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_USAGE,
    GENERATOR,
    GqlRefusal,
)
from record_kind import classify_kind  # noqa: E402
from validate_run import check_episode  # noqa: E402

TINY_SOURCE = """
from pathlib import Path
HOP = [Path("/tmp/other-factory")]
CATALOG_FIRST = 7
PAIRS = [
    {
        "plant": "lattice-tiny",
        "field": "tinyField",
        "coverage": 90,
        "next": "Avoid disable TinyBind.",
        "ok": {
            "slug": "tiny-leftover-bind",
            "surface": "tiny leftover bind",
            "avoid": "Not leftover-GET.",
            "disable": "TinyBind",
            "plan": "Disable TinyBind.",
            "fix": "Rebuild TinyBind.",
            "src": "src/tiny.ts",
            "test": "tests/test_tiny.py",
            "extra": "tests/test_tiny_extra.py",
            "cfg": "src/tiny.yml",
            "bug": "TinyBind leftover",
            "slo": "bind off",
            "residual": "leftover TinyBind",
            "src_obs": "obs",
            "test_obs": "test",
            "fail_obs": "fail",
            "rg_obs": "rg",
            "wrong_edit_old": "old",
            "wrong_edit_new": "new",
            "fix_contents": "fix",
            "suite": 6,
        },
        "bad": {
            "slug": "tiny-leftover-handoff",
            "surface": "tiny leftover handoff",
            "avoid": "Not leftover-GET.",
            "disable": "TinyBind",
            "plan": "Disable then handoff.",
            "fix": "Bind current.",
            "src": "src/tiny.ts",
            "test": "tests/test_tiny.py",
            "extra": "tests/test_tiny_extra.py",
            "cfg": "src/tiny.yml",
            "bug": "TinyBind leftover",
            "slo": "bind off",
            "residual": "leftover TinyBind",
            "src_obs": "obs",
            "test_obs": "test",
            "fail_obs": "fail",
            "rg_obs": "rg",
            "wrong_edit_old": "old",
            "wrong_edit_new": "new",
            "fix_contents": "fix",
            "xfail_note": "union leftover",
        },
    }
]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogLoading(unittest.TestCase):
    def test_committed_catalog_loads_ast_extracted_plants(self):
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(loaded.catalog_id, "gql-plants-v1")
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(len(loaded.plants), 102)
        self.assertEqual(len(loaded.mills), 7)
        self.assertEqual(len({plant.plant_id for plant in loaded.plants}), 102)
        self.assertEqual(loaded.meta["source"]["method"], "git-show+ast.parse")
        self.assertEqual(
            loaded.meta["source"]["commit"],
            "813f93f1969c1c4421e5663492e9663739efa642",
        )
        self.assertEqual(
            [mill.mill_id for mill in loaded.mills],
            [
                "gql_r167",
                "gql_r211",
                "gql_r216",
                "gql_r232",
                "gql_r260",
                "gql_r270",
                "gql_r271",
            ],
        )
        pair = sum(1 for plant in loaded.plants if plant.shape == "pair")
        surface = sum(1 for plant in loaded.plants if plant.shape == "surface")
        self.assertEqual((pair, surface), (38, 64))

    def test_fixture_catalog_is_one_plant(self):
        loaded = catalog.load_catalog(FIXTURE)
        self.assertEqual(loaded.catalog_id, "gql-fixture-v1")
        self.assertEqual(len(loaded.plants), 1)
        self.assertEqual(loaded.plants[0].plant_id, "gql_r0001:lattice-tiny")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="gql-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(FIXTURE, dest)
        meta_path = dest / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(GqlRefusal) as caught:
            catalog.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_CATALOG_SHA256_MISMATCH)

    def test_unknown_plant_is_a_coded_refusal(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self.assertRaises(GqlRefusal) as caught:
            loaded.plant("gql_r0001:missing")
        self.assertEqual(caught.exception.code, FINDING_PLANT_NOT_FOUND)


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_literals_and_skips_hop(self):
        rows = catalog.plants_from_source(
            TINY_SOURCE, mill_id="gql_r0007", source="tiny_source.py"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["plant_id"], "gql_r0007:lattice-tiny")
        self.assertEqual(rows[0]["base_round"], 7)
        self.assertEqual(rows[0]["ok"]["slug"], "tiny-leftover-bind")
        self.assertNotIn("HOP", rows[0])

    def test_plants_from_source_prefers_extra_over_computed_pairs(self):
        source = TINY_SOURCE.replace("PAIRS = [", "EXTRA = [") + "\nPAIRS = unused_pairs()\n"
        rows = catalog.plants_from_source(source, mill_id="gql_r0216", source="extra.py")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["shape"], "pair")

    def test_plants_from_source_refuses_a_call_in_plants(self):
        source = "PAIRS = [dict(plant='x')]\n"
        with self.assertRaises(GqlRefusal) as caught:
            catalog.plants_from_source(source, mill_id="gql_r0001", source="bad.py")
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)

    def test_package_tree_has_no_vendored_or_loop_mills(self):
        tree = PIPELINES / "gql"
        hits = list(tree.rglob("gql-mill-r*.py")) + list(tree.rglob("gql-loop*.py"))
        hits += list(tree.rglob("*leftover*_mill.py"))
        self.assertEqual(hits, [])
        self.assertEqual(list((REPO / "config" / "gql").rglob("gql-mill-r*.py")), [])


class GeneratePairs(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="gql-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_fixture_pair_is_an_episode_and_not_hosted_grok(self):
        dest = self.root / "out"
        request = generate.GenerateRequest(
            FIXTURE, dest, plant_id="gql_r0001:lattice-tiny", round=3
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["pairs"], 1)
        self.assertEqual(summary["generator"], GENERATOR)
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        ok, bad = [json.loads(line) for line in lines]
        self.assertEqual(ok["id"], "gql-r3-tiny-leftover-bind")
        self.assertEqual(bad["id"], "gql-r3-tiny-leftover-handoff")
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(classify_kind(bad), "episode")
        self.assertEqual(check_episode(ok, "ok"), [])
        self.assertEqual(check_episode(bad, "bad"), [])
        self.assertEqual(ok["meta"]["factory"], FACTORY)
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertNotEqual(ok["meta"]["generator"], "grok-4.6")
        self.assertTrue(ok["reward"]["success"])
        self.assertFalse(bad["reward"]["success"])
        self.assertEqual(bad["reward"]["handoff"], 1)
        notes = (dest / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        self.assertIn("Novel coverage: 91%", notes)

    def test_committed_surface_plant_is_an_episode(self):
        dest = self.root / "surface"
        request = generate.GenerateRequest(
            COMMITTED,
            dest,
            plant_id="gql_r232:hasura-inherited-role-after-field-perm",
            round=232,
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        ok, bad = [json.loads(line) for line in lines]
        self.assertEqual(ok["id"], "gql-r232-hasura-inherited-role-after-field-perm")
        self.assertEqual(bad["id"], "gql-r232-hasura-disable-permissions")
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(classify_kind(bad), "episode")
        self.assertEqual(check_episode(ok, "ok"), [])
        self.assertEqual(check_episode(bad, "bad"), [])
        self.assertEqual(len(ok["steps"]), 16)
        self.assertEqual(len(bad["steps"]), 17)
        self.assertNotEqual(ok["meta"]["generator"], "grok-4.6")

    def test_existing_destination_is_refused(self):
        dest = self.root / "exists"
        dest.mkdir()
        with self.assertRaises(GqlRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_EXISTS)

    def test_destination_under_raw_is_refused(self):
        dest = self.root / "outputs" / "raw" / "gql-out"
        with self.assertRaises(GqlRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(dest.exists())

    def test_generate_requires_exactly_one_selector(self):
        dest = self.root / "none"
        with self.assertRaises(GqlRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest))
        self.assertEqual(caught.exception.code, FINDING_USAGE)


class CliSurface(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="gql-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_check_json_on_the_fixture(self):
        code, out, err = invoke(["catalog-check", "--catalog", str(FIXTURE), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 1)
        self.assertEqual(payload["findings"], [])

    def test_generate_json_writes_the_pair(self):
        dest = self.root / "cli-out"
        code, out, err = invoke([
            "generate", "--catalog", str(FIXTURE), "--out", str(dest),
            "--plant", "gql_r0001:lattice-tiny", "--json",
        ])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 2)
        self.assertTrue((dest / generate.RECORDS_FILENAME).is_file())

    def test_missing_catalog_is_exit_two_and_json_on_stdout(self):
        code, out, err = invoke(["catalog-check", "--catalog", "/nonexistent/gql", "--json"])
        self.assertEqual((code, err), (2, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "refused")
        self.assertTrue(payload["code"].startswith("gql."))


class ImportTwins(unittest.TestCase):
    def test_flat_and_package_catalog_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        import pipelines.gql.catalog as packaged

        self.assertIs(packaged, catalog)


if __name__ == "__main__":
    unittest.main()
