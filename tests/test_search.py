#!/usr/bin/env python3
"""FAMILY=search: AST catalog extract of leftover mills (no vendored publishers)."""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from leftover_mill import PUBLISHED_FACTORY_MIX  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from search.catalog import CATALOG  # noqa: E402
from search.catalog_extract import (  # noqa: E402
    SHAPE_PAIR_6TUPLES,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    extract_mill_catalog,
    mill_summary,
)
from search.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from search.sources import MILL_SOURCES, catalog_sources  # noqa: E402
from search import vocabulary as cv  # noqa: E402

_LEFTOVER_SNIPPET = """
'''search-index-rebuild leftover leftover leftover mill r88+.'''
FACTORY = "search-index-rebuild-factory"
GEN = "grok-4.6"
N_ROUNDS = 1
CATALOG_FIRST = 88
HOP = ["email-webhook-retry-factory", "ssl-cert-rotation-factory"]
PAIRS: list[tuple] = [
    (
        (
            "meili-swap-leftover3c-rebuild",
            "Meilisearch leftover leftover leftover catalog-c",
            "drop index",
            "create index + swapIndexes leftover leftover leftover catalog-c",
            "swapIndexes leftover leftover leftover catalog-c; do not drop the live index.",
            "https://www.meilisearch.com/docs/reference/api/swap_indexes",
        ),
        (
            "meili-drop-index-leftover3c-handoff",
            "Meilisearch leftover leftover leftover drop",
            "drop index",
            "nightly drop index leftover leftover leftover catalog-c",
            "Ticket is swapIndexes leftover leftover leftover catalog-c.",
            "https://www.meilisearch.com/docs/reference/api/indexes",
        ),
    ),
]
"""

_PUBLISHER_NAMES = frozenset(
    {
        "build_success",
        "build_partial",
        "candidates",
        "try_reserve",
        "run_one",
        "main",
    }
)


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            [
                "git",
                "show",
                "origin/legacy-mill-lane:experiments/search_index_rebuild_leftover3_mill.py",
            ],
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


def _package_function_names() -> set[str]:
    names: set[str] = set()
    for path in (REPO / "pipelines" / "search").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
    return names


class SearchSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FAMILY, "search")
        self.assertEqual(cv.FAMILY_PREFIX, "sir")
        self.assertEqual(cv.FACTORY, "search-index-rebuild-factory")
        self.assertEqual(cv.GENERATOR, "grok-4.6")
        self.assertEqual(cv.PRESERVE_COMMIT, "e39b5453220fed034c7e112421953e0bf9a18e3d")

    def test_two_leftover_mill_sources(self):
        self.assertEqual(len(MILL_SOURCES), 2)
        self.assertEqual(len(catalog_sources()), 2)
        self.assertEqual(
            [source.mill_id for source in catalog_sources()],
            [
                "search_index_rebuild_leftover3_mill",
                "search_index_rebuild_leftover_lll_mill",
            ],
        )
        self.assertEqual(catalog_sources()[0].catalog_first, 88)
        self.assertEqual(catalog_sources()[1].catalog_first, 108)
        self.assertEqual(catalog_sources()[0].n_hops, 8)
        self.assertEqual(catalog_sources()[1].n_hops, 11)

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(
                path
                for path in REPO.rglob(pattern)
                if "legacy-mill-lane" not in str(path)
            )
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("search_index_rebuild_leftover3_mill.py"))
        self.assertTrue(
            is_vendor_filename("search_index_rebuild_leftover_lll_mill.py")
        )
        self.assertTrue(is_vendor_filename("sir-mill-leftover3-r72.py"))
        self.assertTrue(is_vendor_filename("sir-loop-leftover3-r72.py"))
        self.assertTrue(is_vendor_filename("sir_r108_leftover3d_mill.py"))
        self.assertFalse(is_vendor_filename("sir-mill-r31.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths(
                [Path("experiments/search_index_rebuild_leftover3_mill.py")]
            )

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "search"
        hits = []
        for name in (
            "catalog_ast.py",
            "catalog_extract.py",
            "catalog.py",
            "identity.py",
            "sources.py",
            "vocabulary.py",
            "__init__.py",
        ):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_package_has_no_launderer_publishers(self):
        names = _package_function_names()
        self.assertEqual(names & _PUBLISHER_NAMES, set())
        self.assertFalse((REPO / "pipelines" / "search" / "generate.py").exists())
        self.assertFalse((REPO / "pipelines" / "search" / "cli.py").exists())

    def test_extractor_reads_literal_pairs_and_hops(self):
        extracted = extract_mill_catalog(
            _LEFTOVER_SNIPPET,
            path="experiments/search_index_rebuild_leftover3_mill.py",
        )
        self.assertEqual(extracted["shape"], SHAPE_PAIR_6TUPLES)
        self.assertEqual(extracted["catalog_first"], 88)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["n_hops"], 2)
        self.assertEqual(extracted["first_slug"], "meili-swap-leftover3c-rebuild")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "meili-drop-index-leftover3c-handoff")
        self.assertEqual(extracted["pairs"][0]["success_wrong"], "drop index")
        self.assertTrue(extracted["pairs"][0]["fail_handoff"])
        self.assertEqual(
            extracted["hops"],
            ["email-webhook-retry-factory", "ssl-cert-rotation-factory"],
        )
        self.assertEqual(
            extracted["doc_first_line"],
            "search-index-rebuild leftover leftover leftover mill r88+.",
        )

    def test_extractor_refuses_non_literal_pairs(self):
        source = (
            'FACTORY = "search-index-rebuild-factory"\n'
            'GEN = "grok-4.6"\n'
            "N_ROUNDS = 1\n"
            "CATALOG_FIRST = 88\n"
            'HOP = ["email-webhook-retry-factory"]\n'
            "PAIRS = [leftover_pair()]\n"
        )
        with self.assertRaises(ValueError):
            extract_mill_catalog(
                source, path="experiments/search_index_rebuild_leftover3_mill.py"
            )

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 2)
        self.assertEqual(CATALOG.n_pair_rows, 32)
        self.assertEqual(CATALOG.slice, "leftover-mills")
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        leftover3 = CATALOG.mills["search_index_rebuild_leftover3_mill"]
        leftover_lll = CATALOG.mills["search_index_rebuild_leftover_lll_mill"]
        self.assertEqual(leftover3.n_rows, 16)
        self.assertEqual(leftover3.catalog_first, 88)
        self.assertEqual(leftover3.first_slug, "meili-swap-leftover3c-rebuild")
        self.assertEqual(leftover3.last_slug, "quickwit-split-leftover3c-rebuild")
        self.assertEqual(len(leftover3.pairs), 16)
        self.assertTrue(leftover3.pairs[0]["fail_handoff"])
        self.assertEqual(leftover_lll.n_rows, 16)
        self.assertEqual(leftover_lll.catalog_first, 108)
        self.assertEqual(leftover_lll.first_slug, "quickwit-janitor-leftover-lll-rebuild")
        self.assertEqual(leftover_lll.last_slug, "os-ism-rollover-leftover-lll-rebuild")
        self.assertEqual(leftover3.n_hops, 8)
        self.assertEqual(leftover_lll.n_hops, 11)

    def test_leftover3_slugs_match_published_factory_mix_stems(self):
        leftover3 = CATALOG.mills["search_index_rebuild_leftover3_mill"]
        stems = {
            mix_id.split("-", 2)[-1]
            for mix_id in PUBLISHED_FACTORY_MIX["email-webhook-retry-factory"]
        }
        catalog_slugs = {row["success_slug"] for row in leftover3.pairs}
        catalog_slugs.update(row["fail_slug"] for row in leftover3.pairs)
        self.assertTrue(stems <= catalog_slugs)
        self.assertIn("email-webhook-retry-factory", leftover3.hops)

    def test_hops_are_catalogued_not_executed(self):
        self.assertIn("email-webhook-retry-factory", CATALOG.hops)
        self.assertIn("flaky-test-quarantine-factory", CATALOG.hops)
        self.assertNotIn(cv.FACTORY, CATALOG.hops)
        tree = ast.parse(
            (REPO / "pipelines" / "search" / "catalog_extract.py").read_text(
                encoding="utf-8"
            )
        )
        assigned = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assigned.append(node.name)
        self.assertNotIn("candidates", assigned)
        self.assertNotIn("try_reserve", assigned)
        self.assertNotIn("run_one", assigned)


class SearchLegacyExtractTests(unittest.TestCase):
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
            self.assertEqual(live["hops"], list(committed.hops), source.mill_id)
            mills.append(mill_summary(live, include_pairs=True))
        self.assertEqual(
            dumps_catalog(catalog_document(mills)),
            catalog_json_path().read_text(encoding="utf-8"),
        )

    def test_git_show_is_the_only_legacy_read(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            refuse_vendor_paths(dest.rglob("*") if dest.exists() else ())
            self.assertEqual(list(dest.glob("search_index_rebuild*.py")), [])


if __name__ == "__main__":
    unittest.main()
