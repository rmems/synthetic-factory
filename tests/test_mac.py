#!/usr/bin/env python3
"""MAC leftover mill: AST extract, representative catalog, no vendored mills."""

from __future__ import annotations

import ast
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

from mac import catalog as cat  # noqa: E402
from mac import cli, generate  # noqa: E402
from mac._contract import (  # noqa: E402
    CATALOG_ID,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_AST_NOT_A_PLANT,
    FINDING_VENDOR_PATH,
    GENERATOR,
    SOURCE_COMMIT,
    MacRefusal,
    is_vendor_filename,
    refuse_vendor_paths,
)
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

PACKAGE = PIPELINES / "mac"

P_SNIPPET = """
def P(slug, goal, agents, turns, d, res, joint, novel, dens):
    return locals()

PLANTS = [
    P("wetphos-gypsum-vs-p2o5", "Hold wet-process gypsum without a P2O5 spike.",
      [], [], "d", "res", "joint", True, False),
]
"""

A_SNIPPET = """
def A(slug, process, metric, now, spec, legal, spike, bad, add, mins, hold_n, hold, divert, fail, residual, dens, op, eng, lab, novel):
    return P(slug, f"Hold {process}", [], [], spike, add, mins, True, False)

A("maleic-butane-vs-conv", "maleic", "conversion", "now", "spec", "legal",
  "butane-spike", "bad", "add", 5, 1, "hold", "divert", "fail", "residual",
  False, "op", "eng", "lab", True)
"""

SCEN_SNIPPET = """
SCEN = [
    dict(
        slug="merge-queue-vs-rebase",
        goal="Land leftover merge-queue SHA without a leftover rebase.",
        roles=(("mq_owner", "keep the queue"),),
    )
]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", f"{SOURCE_COMMIT}:experiments/mac-mill-leftover-r3038.py"],
            cwd=REPO,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _module_uses_exec(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id in {"exec", "eval", "compile"}:
            hits.append(f"{path.name}:{node.lineno}:{node.func.id}")
    return hits


class PackageShape(unittest.TestCase):
    def test_the_package_does_not_vendor_mac_mill_scripts(self):
        names = {
            path.name
            for path in PACKAGE.iterdir()
            if path.suffix in {".py", ".json", ".jsonl"}
        }
        self.assertEqual(
            names,
            {
                "CATALOG.json",
                "plants.jsonl",
                "__init__.py",
                "_contract.py",
                "catalog.py",
                "cli.py",
                "generate.py",
            },
        )
        self.assertEqual(list(PACKAGE.glob("mac-mill*.py")), [])
        self.assertEqual(list(PACKAGE.glob("mac-hop-loop*.py")), [])
        self.assertEqual(list(PACKAGE.glob("*mill*.py")), [])

    def test_both_import_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.mac import catalog as packaged

        self.assertIs(packaged, cat)
        self.assertIs(sys.modules["mac.catalog"], sys.modules["pipelines.mac.catalog"])

    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)
        self.assertEqual(FACTORY, "multi-agent-coordination-factory")
        self.assertEqual(GENERATOR, "grok-4.6")

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("mac-mill-r3034.py"))
        self.assertTrue(is_vendor_filename("mac-mill-leftover-r3038.py"))
        self.assertTrue(is_vendor_filename("mac-hop-loop-r3034.py"))
        self.assertTrue(is_vendor_filename("mac_r3267_leftover3_swcoord_mill.py"))
        self.assertFalse(is_vendor_filename("generate.py"))
        with self.assertRaises(MacRefusal) as ctx:
            refuse_vendor_paths([Path("experiments/mac-mill-r3034.py")])
        self.assertEqual(ctx.exception.code, FINDING_VENDOR_PATH)

    def test_extractor_modules_never_exec(self):
        hits = []
        for name in ("_contract.py", "catalog.py", "generate.py", "cli.py", "__init__.py"):
            hits.extend(_module_uses_exec(PACKAGE / name))
        self.assertEqual(hits, [])


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_p_calls(self):
        plants = generate.plants_from_source(P_SNIPPET)
        self.assertEqual(plants[0]["shape"], generate.SHAPE_P)
        self.assertEqual(plants[0]["slug"], "wetphos-gypsum-vs-p2o5")
        self.assertIn("P2O5", plants[0]["goal"])

    def test_plants_from_source_reads_a_calls_not_inner_p(self):
        plants = generate.plants_from_source(A_SNIPPET)
        self.assertEqual(len(plants), 1)
        self.assertEqual(plants[0]["shape"], generate.SHAPE_A)
        self.assertEqual(plants[0]["slug"], "maleic-butane-vs-conv")
        self.assertEqual(plants[0]["process"], "maleic")
        self.assertEqual(plants[0]["spike"], "butane-spike")

    def test_plants_from_source_reads_leftover3_scen(self):
        plants = generate.plants_from_source(SCEN_SNIPPET)
        self.assertEqual(plants[0]["shape"], generate.SHAPE_SCEN)
        self.assertEqual(plants[0]["slug"], "merge-queue-vs-rebase")

    def test_a_module_without_catalog_rows_is_refused(self):
        with self.assertRaises(MacRefusal) as ctx:
            generate.plants_from_source("FACTORY = 'multi-agent-coordination-factory'\n")
        self.assertEqual(ctx.exception.code, FINDING_AST_NOT_A_PLANT)


class CommittedCatalog(unittest.TestCase):
    def test_full_identity_jsonl_and_source_pins(self):
        loaded = cat.load_catalog()
        report = cat.catalog_check()
        self.assertEqual(loaded.catalog_id, CATALOG_ID)
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(len(loaded.plants), 1401)
        self.assertEqual(len(loaded.sources), 32)
        self.assertEqual(loaded.extract.get("slice"), "full")
        self.assertEqual(loaded.extract.get("deferred_rows"), 0)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], 1401)
        self.assertEqual(report["deferred_rows"], 0)
        self.assertEqual(report["full_row_count"], 1401)
        self.assertEqual(report["catalog_files"], 31)
        self.assertFalse(report["exec"])
        self.assertEqual(loaded.plants[0].slug, "wetphos-gypsum-vs-p2o5")
        maleic = next(plant for plant in loaded.plants if plant.slug == "maleic-butane-vs-conv")
        self.assertEqual(maleic.process, "maleic anhydride")
        self.assertEqual(maleic.metric, "conv")
        self.assertEqual(maleic.spike, "14 K")
        self.assertTrue(any(plant.slug == "merge-queue-vs-rebase" for plant in loaded.plants))
        keys = [f"{plant.source}:{plant.slug}" for plant in loaded.plants]
        self.assertEqual(len(keys), len(set(keys)))

    def test_leftover_sources_reextract_the_committed_jsonl_rows(self):
        if not _legacy_available():
            self.skipTest("legacy-mill-lane mac mills are not in this environment")
        samples = (
            ("experiments/mac-mill-leftover-r3038.py", "leftover-r3038"),
            ("experiments/mac-mill-r3205.py", "r3205"),
            ("experiments/mac_r3267_leftover3_swcoord_mill.py", "leftover3-scen"),
        )
        committed = cat.load_catalog().plants
        by_source: dict[str, list[cat.Plant]] = {}
        for plant in committed:
            by_source.setdefault(plant.source, []).append(plant)
        for path, _label in samples:
            text = subprocess.check_output(
                ["git", "show", f"{SOURCE_COMMIT}:{path}"],
                cwd=REPO,
                text=True,
            )
            extracted = generate.plants_from_source(text)
            pinned = by_source[path]
            self.assertEqual(len(pinned), len(extracted))
            for row, plant in zip(extracted, pinned, strict=True):
                self.assertEqual(plant.slug, row["slug"])
                self.assertEqual(plant.shape, row["shape"])
                if row["shape"] == generate.SHAPE_A:
                    self.assertEqual(plant.process, row["process"])
                    self.assertEqual(plant.metric, row["metric"])
                    self.assertEqual(plant.spike, row["spike"])
                else:
                    self.assertEqual(plant.goal, row["goal"])


class Cli(unittest.TestCase):
    def test_catalog_check_json_reports_the_slice(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 1401)
        self.assertEqual(payload["deferred_rows"], 0)
        self.assertEqual(payload["full_row_count"], 1401)

    def test_extract_json_from_a_p_snippet(self):
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix="-mac-snippet.py", delete=False
        )
        handle.write(P_SNIPPET)
        handle.close()
        snippet = Path(handle.name)
        self.addCleanup(snippet.unlink)
        code, out, err = invoke(["extract", "--source", str(snippet), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"][0]["slug"], "wetphos-gypsum-vs-p2o5")


if __name__ == "__main__":
    unittest.main()
