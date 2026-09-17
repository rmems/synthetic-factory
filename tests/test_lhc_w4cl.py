#!/usr/bin/env python3
"""FAMILY=lhc slot 6: AST catalog extract of w4cl-r4605 (no vendored publisher)."""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from lhc_w4cl.catalog import CATALOG  # noqa: E402
from lhc_w4cl.catalog_extract import (  # noqa: E402
    SHAPE_PLANTS_MK_FN,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    extract_mill_catalog,
    mill_summary,
)
from lhc_w4cl.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from lhc_w4cl.sources import MILL_SOURCES, catalog_sources  # noqa: E402
from lhc_w4cl import vocabulary as cv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_W4CL_SNIPPET = '''
"""Grok 4.6 LHC mill w4cl: unused storage/mesh/CI/OLTP plants after w4ck."""
USED_FROM = 4163

def mk(ok, slug, plant, what, impl, src, sym, grep, grep_obs, fail1, wrong, insight):
    return {"ok": ok, "slug": slug, "plant": plant}

def fn(key):
    def inner(rnd, k=key):
        return PLANTS[k]
    return inner

PLANTS = {
    "ceph": mk(
        True, "pr-ceph-osd-memory-target-bytes", "lock-cephmem",
        "w", "i", "s", "y", "g", "o", "f", "x", "n",
    ),
    "minio": mk(
        False, "pr-minio-erasure-set-drive-count", "quay-minerset",
        "w", "i", "s", "y", "g", "o", "f", "x", "n",
    ),
}

LHC_PAIRS = [
    ("Ceph osd_memory_target vs MinIO erasure set", fn("ceph"), fn("minio"), "d", "l", "n"),
]
'''

_PUBLISHER_NAMES = frozenset(
    {
        "try_reserve",
        "publish_round",
        "hop_targets",
        "emit_lhc",
        "write_stage",
        "main",
        "plant_from",
        "expand",
    }
)


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            [
                "git",
                "show",
                "origin/legacy-mill-lane:experiments/lhc-mill-w4cl-r4605.py",
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
    for path in (REPO / "pipelines" / "lhc_w4cl").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
    return names


class LhcW4clSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FAMILY, "lhc")
        self.assertEqual(cv.FAMILY_PREFIX, "lhc")
        self.assertEqual(cv.FACTORY, "long-horizon-coding-factory")
        self.assertEqual(cv.GENERATOR, "grok-4.6")
        self.assertEqual(cv.SLICE_ID, "w4cl-r4605")
        self.assertEqual(cv.PRESERVE_COMMIT, "813f93f1969c1c4421e5663492e9663739efa642")

    def test_one_w4cl_mill_source(self):
        self.assertEqual(len(MILL_SOURCES), 1)
        self.assertEqual(len(catalog_sources()), 1)
        source = catalog_sources()[0]
        self.assertEqual(source.mill_id, "lhc-mill-w4cl-r4605")
        self.assertEqual(source.catalog_first, 4605)
        self.assertEqual(source.n_rows, 24)
        self.assertEqual(source.n_plants, 48)
        self.assertEqual(
            source.blob_sha, "221cef84404e8249e80cdbb4bfb41ce1955a4c2f"
        )

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
        self.assertTrue(is_vendor_filename("lhc-mill-w4cl-r4605.py"))
        self.assertTrue(is_vendor_filename("lhc-loop-w4cl.py"))
        self.assertTrue(is_vendor_filename("lhc_r4605_mill.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        self.assertFalse(is_vendor_filename("lhc_w4cl.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/lhc-mill-w4cl-r4605.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "lhc_w4cl"
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
        self.assertFalse((REPO / "pipelines" / "lhc_w4cl" / "generate.py").exists())
        self.assertFalse((REPO / "pipelines" / "lhc_w4cl" / "cli.py").exists())

    def test_extractor_reads_mk_plants_and_fn_pairs(self):
        extracted = extract_mill_catalog(
            _W4CL_SNIPPET,
            path="experiments/lhc-mill-w4cl-r4605.py",
        )
        self.assertEqual(extracted["shape"], SHAPE_PLANTS_MK_FN)
        self.assertEqual(extracted["catalog_first"], 4605)
        self.assertEqual(extracted["used_from"], 4163)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["n_plants"], 2)
        self.assertEqual(extracted["first_slug"], "pr-ceph-osd-memory-target-bytes")
        self.assertEqual(extracted["last_slug"], "pr-ceph-osd-memory-target-bytes")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "pr-minio-erasure-set-drive-count")
        self.assertEqual(extracted["pairs"][0]["success_plant"], "lock-cephmem")
        self.assertEqual(extracted["plants"][0]["key"], "ceph")
        self.assertTrue(extracted["plants"][0]["ok"])
        self.assertFalse(extracted["plants"][1]["ok"])
        self.assertEqual(
            extracted["doc_first_line"],
            "Grok 4.6 LHC mill w4cl: unused storage/mesh/CI/OLTP plants after w4ck.",
        )

    def test_extractor_refuses_non_mk_plants(self):
        source = (
            "USED_FROM = 4163\n"
            "PLANTS = {\"ceph\": load()}\n"
            "LHC_PAIRS = []\n"
        )
        with self.assertRaises(ValueError):
            extract_mill_catalog(source, path="experiments/lhc-mill-w4cl-r4605.py")

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 1)
        self.assertEqual(CATALOG.n_pair_rows, 24)
        self.assertEqual(CATALOG.n_plant_rows, 48)
        self.assertEqual(CATALOG.slice, "w4cl-r4605")
        self.assertEqual(CATALOG.family, "lhc")
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        mill = CATALOG.mills["lhc-mill-w4cl-r4605"]
        self.assertEqual(mill.n_rows, 24)
        self.assertEqual(mill.n_plants, 48)
        self.assertEqual(mill.catalog_first, 4605)
        self.assertEqual(mill.used_from, 4163)
        self.assertEqual(mill.first_slug, "pr-ceph-osd-memory-target-bytes")
        self.assertEqual(mill.last_slug, "pr-meilisearch-max-indexing-memory")
        self.assertEqual(len(mill.pairs), 24)
        self.assertEqual(len(mill.plants), 48)
        self.assertEqual(mill.pairs[0]["success_key"], "ceph")
        self.assertEqual(mill.pairs[-1]["fail_key"], "typesense")
        self.assertEqual(mill.shape, SHAPE_PLANTS_MK_FN)


class LhcW4clLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        source = catalog_sources()[0]
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
        self.assertEqual(live["n_rows"], committed.n_rows)
        self.assertEqual(live["n_plants"], committed.n_plants)
        self.assertEqual(live["first_slug"], committed.first_slug)
        self.assertEqual(live["last_slug"], committed.last_slug)
        self.assertEqual(live["catalog_first"], committed.catalog_first)
        self.assertEqual(live["used_from"], committed.used_from)
        self.assertEqual(live["sha256"], committed.sha256)
        self.assertEqual(live["shape"], committed.shape)
        self.assertEqual(
            dumps_catalog(
                catalog_document(
                    [mill_summary(live, include_pairs=True, include_plants=True)]
                )
            ),
            catalog_json_path().read_text(encoding="utf-8"),
        )

    def test_git_show_is_the_only_legacy_read(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            refuse_vendor_paths(dest.rglob("*") if dest.exists() else ())
            self.assertEqual(list(dest.glob("lhc-mill*.py")), [])


if __name__ == "__main__":
    unittest.main()
