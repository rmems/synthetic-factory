#!/usr/bin/env python3
"""RAG mill package: catalog pins, AST extract, generate, CLI, no leftover mills."""

from __future__ import annotations

import ast
import contextlib
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
FIXTURE = REPO / "tests" / "fixtures" / "rag"
COMMITTED = REPO / "config" / "rag"
LEGACY_REF = "origin/legacy-mill-lane"
LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
LEGACY_MILL = "experiments/rag-mill-lll-r670.py"
LEGACY_LOOP = "experiments/rag-loop-r343.py"

sys.path.insert(0, str(PIPELINES))

from rag import catalog, cli, generate  # noqa: E402
from rag._contract import (  # noqa: E402
    FACTORY,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_USAGE,
    GENERATOR,
    LEGACY_LOOP as CONTRACT_LOOP,
    LEGACY_SOURCE,
    RagRefusal,
)
from record_kind import classify_kind  # noqa: E402
from validate_run import check_episode  # noqa: E402

TINY_SOURCE = """
FACTORY = "rag-retrieval-debug-factory"
CATALOG_FIRST = 7
PAIRS = [
    P("qdrant", "payload", "QD-PL-1", "QD-PL-2"),
]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def _git_show(path: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "show", f"{LEGACY_REF}:{path}"],
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


class CatalogLoading(unittest.TestCase):
    def test_committed_catalog_loads_sixteen_ast_extracted_plants(self):
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(loaded.catalog_id, "rag-lll-v1")
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(len(loaded.plants), 16)
        self.assertEqual(len(loaded.mills), 1)
        self.assertEqual(len({plant.plant_id for plant in loaded.plants}), 16)
        self.assertEqual(loaded.meta["source"]["method"], "git-show+ast.parse")
        self.assertEqual(loaded.meta["source"]["commit"], LEGACY_COMMIT)
        self.assertEqual([mill.mill_id for mill in loaded.mills], ["rag_r670"])
        self.assertEqual(loaded.plants[0].eng, "qdrant")
        self.assertEqual(loaded.plants[0].leftover, "payload")
        self.assertEqual(loaded.plants[-1].slug, "qdrant-scroll")

    def test_fixture_catalog_is_one_plant(self):
        loaded = catalog.load_catalog(FIXTURE)
        self.assertEqual(loaded.catalog_id, "rag-fixture-v1")
        self.assertEqual(len(loaded.plants), 1)
        self.assertEqual(loaded.plants[0].plant_id, "rag_r0001:qdrant-payload")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="rag-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(FIXTURE, dest)
        meta_path = dest / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(RagRefusal) as caught:
            catalog.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_CATALOG_SHA256_MISMATCH)

    def test_unknown_plant_is_a_coded_refusal(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self.assertRaises(RagRefusal) as caught:
            loaded.plant("rag_r0001:missing")
        self.assertEqual(caught.exception.code, FINDING_PLANT_NOT_FOUND)


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_p_calls_and_catalog_first(self):
        rows = catalog.plants_from_source(
            TINY_SOURCE, mill_id="rag_r0007", source="tiny_source.py"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["plant_id"], "rag_r0007:qdrant-payload")
        self.assertEqual(rows[0]["base_round"], 7)
        self.assertEqual(rows[0]["ticket_ok"], "QD-PL-1")
        self.assertEqual(rows[0]["ticket_fail"], "QD-PL-2")
        ok, fail = catalog.expand_pair("qdrant", "payload", "QD-PL-1", "QD-PL-2")
        self.assertEqual(ok["slug"], "qdrant-leftover-payload-filter-lll")
        self.assertEqual(fail["slug"], "qdrant-drop-payload-handoff-lll")
        self.assertTrue(ok["token"].startswith("TESTONLY_"))

    def test_plants_from_source_refuses_a_non_p_call(self):
        source = "PAIRS = [dict(eng='qdrant')]\n"
        with self.assertRaises(RagRefusal) as caught:
            catalog.plants_from_source(source, mill_id="rag_r0001", source="bad.py")
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)

    def test_legacy_mill_ast_matches_committed_catalog(self):
        text = _git_show(LEGACY_MILL)
        if text is None:
            self.skipTest(f"{LEGACY_REF}:{LEGACY_MILL} is not available")
        rows = catalog.plants_from_source(
            text, mill_id="rag_r670", source=LEGACY_MILL
        )
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(len(rows), 16)
        self.assertEqual([row["slug"] for row in rows], [plant.slug for plant in loaded.plants])
        self.assertEqual(
            [(row["eng"], row["leftover"], row["ticket_ok"], row["ticket_fail"]) for row in rows],
            [
                (plant.eng, plant.leftover, plant.ticket_ok, plant.ticket_fail)
                for plant in loaded.plants
            ],
        )
        self.assertEqual(rows[0]["base_round"], 670)

    def test_legacy_loop_is_not_a_pairs_catalog_and_is_not_execed(self):
        text = _git_show(LEGACY_LOOP)
        if text is None:
            self.skipTest(f"{LEGACY_REF}:{LEGACY_LOOP} is not available")
        tree = ast.parse(text)
        self.assertTrue(any(isinstance(node, ast.Import) and any(
            alias.name == "runpy" for alias in node.names
        ) for node in ast.walk(tree)))
        with self.assertRaises(RagRefusal) as caught:
            catalog.plants_from_source(text, mill_id="rag_r0343", source=LEGACY_LOOP)
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)
        self.assertEqual(CONTRACT_LOOP, LEGACY_LOOP)
        self.assertEqual(LEGACY_SOURCE, LEGACY_MILL)

    def test_package_tree_has_no_vendored_mill_or_loop_scripts(self):
        hits = list((PIPELINES / "rag").rglob("rag-*.py"))
        hits += list((PIPELINES / "rag").rglob("*leftover*_mill.py"))
        hits += list((REPO / "config" / "rag").rglob("rag-*.py"))
        self.assertEqual(hits, [])
        forbidden = ("exec(", "eval(", "runpy", "compile(")
        for path in (PIPELINES / "rag").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, msg=f"{path.name} contains {token}")


class GeneratePairs(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="rag-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_fixture_pair_is_an_episode_and_not_hosted_grok(self):
        dest = self.root / "out"
        request = generate.GenerateRequest(
            FIXTURE, dest, plant_id="rag_r0001:qdrant-payload", round=3
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["pairs"], 1)
        self.assertEqual(summary["generator"], GENERATOR)
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        ok, bad = [json.loads(line) for line in lines]
        self.assertEqual(ok["id"], "rag-r3-qdrant-leftover-payload-filter-lll")
        self.assertEqual(bad["id"], "rag-r3-qdrant-drop-payload-handoff-lll")
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(classify_kind(bad), "episode")
        self.assertEqual(check_episode(ok, "ok"), [])
        self.assertEqual(check_episode(bad, "bad"), [])
        self.assertEqual(ok["meta"]["factory"], FACTORY)
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertNotEqual(ok["meta"]["generator"], "grok-4.6")
        self.assertTrue(ok["reward"]["success"])
        self.assertEqual(len(ok["steps"]), 14)
        self.assertFalse(bad["reward"]["success"])
        self.assertEqual(bad["reward"]["handoff"], 1)
        self.assertEqual(len(bad["steps"]), 15)
        notes = (dest / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        self.assertIn("Novel coverage: 41%", notes)
        self.assertIn("Not ingest-field", notes)

    def test_existing_destination_is_refused(self):
        dest = self.root / "exists"
        dest.mkdir()
        with self.assertRaises(RagRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_EXISTS)

    def test_destination_under_raw_is_refused(self):
        dest = self.root / "outputs" / "raw" / "rag-out"
        with self.assertRaises(RagRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(dest.exists())

    def test_generate_requires_exactly_one_selector(self):
        dest = self.root / "none"
        with self.assertRaises(RagRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest))
        self.assertEqual(caught.exception.code, FINDING_USAGE)


class CliSurface(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="rag-cli-"))
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
            "--plant", "rag_r0001:qdrant-payload", "--json",
        ])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 2)
        self.assertTrue((dest / generate.RECORDS_FILENAME).is_file())

    def test_missing_catalog_is_exit_two_and_json_on_stdout(self):
        code, out, err = invoke(["catalog-check", "--catalog", "/nonexistent/rag", "--json"])
        self.assertEqual((code, err), (2, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "refused")
        self.assertTrue(payload["code"].startswith("rag."))


class ImportTwins(unittest.TestCase):
    def test_flat_and_package_catalog_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        import pipelines.rag.catalog as packaged

        self.assertIs(packaged, catalog)


if __name__ == "__main__":
    unittest.main()
