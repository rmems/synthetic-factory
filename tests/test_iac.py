#!/usr/bin/env python3
"""PR-a: AST catalog extract and ``pipelines/iac`` skeleton (no vendored mills)."""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from iac.catalog import CATALOG  # noqa: E402
from iac.catalog_extract import (  # noqa: E402
    SHAPE_K8S_CLI_SPEC,
    SHAPE_LEFTOVER,
    SHAPE_LITERAL,
    SHAPE_SUC_FAIL,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    extract_companion_path,
    extract_mill_catalog,
    mill_summary,
)
from iac.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from iac.sources import MILL_SOURCES, catalog_sources, gen_sources, loop_sources  # noqa: E402
from iac import vocabulary as cv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_R609_SNIPPET = """
FACTORY = "infra-as-code-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 625
PAIRS: list[tuple[dict, dict]] = [
    (
        {"slug": "keep-a", "plant": "alpha-prod", "wrong_b": "Plan: a", "fix_b": "Reflection: a"},
        {"slug": "keep-a-fail", "plant": "alpha-jobs", "handoff": True,
         "wrong_b": "Plan: a", "fix_b": "Reflection: a"},
    ),
    (
        {"slug": "drop-me", "plant": "beta-prod", "wrong_b": "Plan: b", "fix_b": "Reflection: b"},
        {"slug": "drop-me-fail", "plant": "beta-jobs", "handoff": True,
         "wrong_b": "Plan: b", "fix_b": "Reflection: b"},
    ),
]
_DROP_SUCCESS = {"drop-me"}
PAIRS = [pair for pair in PAIRS if pair[0]["slug"] not in _DROP_SUCCESS]
_EXTRA: list[tuple[dict, dict]] = [
    (
        {"slug": "extra-a", "plant": "gamma-prod", "wrong_b": "Plan: c", "fix_b": "Reflection: c"},
        {"slug": "extra-a-fail", "plant": "gamma-jobs", "handoff": True,
         "wrong_b": "Plan: c", "fix_b": "Reflection: c"},
    ),
]
PAIRS.extend(_EXTRA)
"""

_SUC_FAIL_SNIPPET = """
CATALOG_FIRST = 659
PAIRS: list[tuple[dict, dict]] = [
    (
        _suc(slug="atmos-tfvars-vs-stale-stack", plant="firn-prod"),
        _fail(slug="atmos-webold-tfvars-leftover", plant="firn-jobs", handoff=True),
    ),
]
"""

_LEFTOVER_SNIPPET = """
CATALOG_FIRST = 709
PAIRS: list[tuple[dict, dict]] = [
    leftover_pair(s="xp-comprev-vs-old", fs="xp-comprev-old-leftover", g="oxbow", m="xp"),
]
"""

_K8S_SNIPPET = """
CATALOG_FIRST = 1132
K8S: list[tuple] = [
    ("argocd-app-vs-old", "agate", "argocd", "Argo CD Application",
     "Application", "application", "argoproj.io", "agate",
     "argocd-old", "argocd-jobs-old", "argocd", "spec", "fail"),
]
CLI_SPEC: list[dict] = [
    {"s": "lima-inst-vs-old", "g": "cuckoo", "m": "lima", "product": "lima leftover"},
]
CLI: list[tuple[dict, dict]] = [tool_pair(**row) for row in CLI_SPEC]
PAIRS: list[tuple[dict, dict]] = [k8s_pair(*row) for row in K8S] + CLI
"""


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", "origin/legacy-mill-lane:experiments/iac-mill-r609.py"],
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


class IacSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FACTORY, "infra-as-code-factory")
        self.assertEqual(cv.GENERATOR, "grok-4.6")
        self.assertEqual(cv.PRESERVE_COMMIT, "51bc810cd2cdd753e97b1ae737d5fa5b00b92478")

    def test_fifteen_sources_split_into_mills_loops_and_gens(self):
        self.assertEqual(len(MILL_SOURCES), 15)
        self.assertEqual(len(catalog_sources()), 7)
        self.assertEqual(len(loop_sources()), 6)
        self.assertEqual(len(gen_sources()), 2)
        self.assertEqual(
            {source.companion_mill_path for source in loop_sources()},
            {
                "experiments/iac-mill-r609.py",
                "experiments/iac-mill-r683.py",
                "experiments/iac-mill-r709.py",
                "experiments/iac-mill-r1514.py",
            },
        )

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path))
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("iac-mill-r609.py"))
        self.assertTrue(is_vendor_filename("iac-loop-r609.py"))
        self.assertTrue(is_vendor_filename("_gen_iac_plants_r1132.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/iac-mill-r609.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "iac"
        hits = []
        for name in ("catalog_ast.py", "catalog_extract.py", "catalog.py", "identity.py"):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_extractor_rebuilds_literal_drop_and_extend(self):
        extracted = extract_mill_catalog(_R609_SNIPPET, path="experiments/iac-mill-r609.py")
        self.assertEqual(extracted["shape"], SHAPE_LITERAL)
        self.assertEqual(extracted["catalog_first"], 625)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "keep-a")
        self.assertEqual(extracted["last_slug"], "extra-a")
        self.assertEqual(extracted["pairs"][0]["fail_plant"], "alpha-jobs")
        slugs = [row["success_slug"] for row in extracted["pairs"]]
        self.assertNotIn("drop-me", slugs)

    def test_extractor_reads_suc_fail_kwargs(self):
        extracted = extract_mill_catalog(_SUC_FAIL_SNIPPET, path="experiments/iac-mill-r659.py")
        self.assertEqual(extracted["shape"], SHAPE_SUC_FAIL)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "atmos-tfvars-vs-stale-stack")
        self.assertTrue(extracted["pairs"][0]["fail_handoff"])

    def test_extractor_reads_leftover_pair_kwargs(self):
        extracted = extract_mill_catalog(_LEFTOVER_SNIPPET, path="experiments/iac-mill-r709.py")
        self.assertEqual(extracted["shape"], SHAPE_LEFTOVER)
        self.assertEqual(extracted["pairs"][0]["success_plant"], "oxbow-prod")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "xp-comprev-old-leftover")

    def test_extractor_reads_k8s_and_cli_spec_tables(self):
        extracted = extract_mill_catalog(_K8S_SNIPPET, path="experiments/iac-mill-r1132.py")
        self.assertEqual(extracted["shape"], SHAPE_K8S_CLI_SPEC)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "argocd-app-vs-old")
        self.assertEqual(extracted["last_slug"], "lima-inst-vs-old")
        self.assertEqual(extracted["pairs"][0]["success_plant"], "agate-prod")

    def test_loop_mill_path_constant(self):
        source = (
            "ROOT = Path(__file__).resolve().parents[1]\n"
            'MILL = ROOT / "experiments" / "iac-mill-r609.py"\n'
        )
        self.assertEqual(extract_companion_path(source), "experiments/iac-mill-r609.py")

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 7)
        self.assertEqual(CATALOG.n_pair_rows, 1986)
        self.assertEqual(CATALOG.slice, "r609")
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        r609 = CATALOG.mills["iac-mill-r609"]
        self.assertEqual(r609.n_rows, 34)
        self.assertEqual(r609.catalog_first, 625)
        self.assertEqual(r609.first_slug, "flux-helmrelease-vs-helmchart")
        self.assertEqual(r609.last_slug, "cts-consul-vs-stale-task")
        self.assertEqual(len(r609.pairs), 34)
        self.assertTrue(r609.pairs[0]["fail_handoff"])
        self.assertEqual(CATALOG.mills["iac-mill-r1514"].n_rows, 1097)
        self.assertEqual(CATALOG.mills["iac-mill-r683"].n_keep, 9)
        self.assertEqual(CATALOG.mills["iac-mill-r777"].n_rows, 355)
        self.assertFalse(CATALOG.mills["iac-mill-r1514"].pairs)


class IacLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        mills = []
        for source in catalog_sources():
            text = subprocess.check_output(
                ["git", "show", f"{cv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            blob = subprocess.check_output(
                ["git", "rev-parse", f"{cv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            ).strip()
            self.assertEqual(blob, source.blob_sha, source.mill_id)
            live = extract_mill_catalog(text, path=source.path, blob_sha=source.blob_sha)
            committed = CATALOG.mills[source.mill_id]
            self.assertEqual(live["n_rows"], committed.n_rows, source.mill_id)
            self.assertEqual(live["first_slug"], committed.first_slug, source.mill_id)
            self.assertEqual(live["last_slug"], committed.last_slug, source.mill_id)
            self.assertEqual(live["catalog_first"], committed.catalog_first, source.mill_id)
            self.assertEqual(live["sha256"], committed.sha256, source.mill_id)
            self.assertEqual(live["shape"], committed.shape, source.mill_id)
            mills.append(
                mill_summary(live, include_pairs=source.mill_id == "iac-mill-r609")
            )
        self.assertEqual(
            dumps_catalog(catalog_document(mills)),
            catalog_json_path().read_text(encoding="utf-8"),
        )

    def test_loop_and_gen_scripts_name_companion_mills(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        for source in (*loop_sources(), *gen_sources()):
            text = subprocess.check_output(
                ["git", "show", f"{cv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            self.assertEqual(
                extract_companion_path(text),
                source.companion_mill_path,
                source.mill_id,
            )

    def test_git_show_is_the_only_legacy_read(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            refuse_vendor_paths(dest.rglob("*") if dest.exists() else ())
            self.assertEqual(list(dest.glob("iac-mill*.py")), [])


if __name__ == "__main__":
    unittest.main()
