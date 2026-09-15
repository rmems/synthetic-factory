#!/usr/bin/env python3
"""PR-a: AST catalog extract and ``pipelines/lhc`` skeleton (no vendored mills)."""

from __future__ import annotations

import ast
import shutil
import subprocess  # nosec B404 -- git show of pinned legacy-mill-lane blobs only.
import sys
import tempfile
import unittest
from pathlib import Path

_GIT = shutil.which("git")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from lhc.catalog import CATALOG, catalog_json_path, dumps_catalog  # noqa: E402
from lhc.catalog_extract import (  # noqa: E402
    SHAPE_PAIRS_FN_PAIR,
    SHAPE_PAIRS_NAMED,
    SHAPE_PLANTS_MK_FN,
    SHAPE_PLANTS_NAMED,
    SHAPE_PLANTS_P_FN,
    catalog_document,
    extract_mill_catalog,
    is_slice_mill,
    mill_summary,
)
from lhc.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from lhc.sources import MILL_SOURCES, catalog_sources  # noqa: E402
from lhc import vocabulary as cv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_NAMED_SNIPPET = """
USED_FROM = 4163
def pnpm_peer(rnd):
    return expand(rnd, {"slug": "pr-pnpm-peer-auto-install-strict", "plant": "lock-pnpmp",
                        "success": True})
def bun_lock(rnd):
    return expand(rnd, {"slug": "pr-bun-lockfile-text-workspace-proto", "plant": "quay-bunlk",
                        "success": True})
LHC_PAIRS = [
    ("pnpm single React vs Bun workspace lock",
     pnpm_peer, bun_lock,
     "auto-install-peers false", "pnpm packageExtensions", "pnpm dump peer"),
]
"""

_PLANTS_NAMED_SNIPPET = """
USED_FROM = 4163
def P(ok, **k):
    k["ok"] = ok
    return k
PLANTS = {
    "poetry": P(True, slug="pr-poetry-extras-marker-file-missing", plant="lock-poetryx"),
    "pdm": P(True, slug="pr-pdm-lock-update-reuse-stale", plant="lock-pdmupd"),
}
def poetry_extras(rnd):
    return plant_from(rnd, PLANTS["poetry"])
def pdm_lock(rnd):
    return plant_from(rnd, PLANTS["pdm"])
LHC_PAIRS = [
    ("Poetry extras vs PDM lock",
     poetry_extras, pdm_lock,
     "packages include", "pip -e", "poetry dump"),
]
"""

_P_FN_SNIPPET = """
USED_FROM = 4163
def P(ok, **k):
    k["ok"] = ok
    return k
def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    return f
PLANTS = {
    "hatch": P(True, slug="pr-hatch-env-scripts-extra-deps", plant="lock-hatch"),
    "uv": P(True, slug="pr-uv-sync-python-pin", plant="lock-uvsync"),
}
LHC_PAIRS = [
    ("Hatch extra-dependencies vs uv sync",
     fn("hatch"), fn("uv"),
     "extra-dependencies", "uv python pin", "hatch dump"),
]
"""

_MK_FN_SNIPPET = """
USED_FROM = 4163
def mk(ok, slug, plant, what, impl, src, sym, grep, grep_obs, fail1, wrong, insight):
    return {"ok": ok, "slug": slug, "plant": plant}
def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    return f
PLANTS = {
    "fiona": mk(
        True, "pr-fiona-layer-crs", "lock-ficrs",
        "w", "i", "s", "y", "g", "o", "f", "r", "n",
    ),
    "pyogrio": mk(
        True, "pr-pyogrio-use-arrow", "lock-pyog",
        "w", "i", "s", "y", "g", "o", "f", "r", "n",
    ),
}
LHC_PAIRS = [
    ("Fiona crs vs pyogrio use_arrow",
     fn("fiona"), fn("pyogrio"),
     "crs EPSG", "open shp", "fiona dump"),
]
"""

_FN_PAIR_SNIPPET = """
def fn_pair(slug_a, slug_b, plant_a, plant_b, what_a, what_b, impl_a, impl_b,
            src_a, src_b, sym_a, sym_b, grep_a, grep_b, go_a, go_b,
            fail_a, fail_b, wrong_a, wrong_b, ins_a, ins_b):
    def fa(rnd):
        return plant_from(rnd, {})
    def fb(rnd):
        return plant_from(rnd, {})
    return fa, fb
PAIRS = []
fa, fb = fn_pair(
    "protobuf-reserved-field-tombstone", "protobuf-json-name-leftover-alias",
    "protobuf-reserved", "protobuf-json-name",
    "what-a", "what-b", "impl-a", "impl-b", "src-a", "src-b",
    "sym-a", "sym-b", "grep-a", "grep-b", "go-a", "go-b",
    "fail-a", "fail-b", "wrong-a", "wrong-b", "ins-a", "ins-b",
)
PAIRS.append(("protobuf reserved tombstone vs json_name leftover leftover leftover alias",
              fa, fb, "densify", "loops", "next"))
"""


def _git_output(*args: str) -> str:
    if _GIT is None:
        raise FileNotFoundError("git")
    return subprocess.check_output(  # nosec B603 -- fixed git argv, no shell
        [_GIT, *args],
        text=True,
        cwd=REPO,
        stderr=subprocess.DEVNULL,
    )


def _legacy_available() -> bool:
    if _GIT is None:
        return False
    try:
        _git_output("show", f"{cv.LEGACY_REF}:experiments/lhc-mill-w4x-r4358.py")
        return True
    except subprocess.CalledProcessError:
        return False


class _ForbiddenCallFinder(ast.NodeVisitor):
    """Collect ``exec`` / ``eval`` / ``compile`` calls; used only in tests."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.hits: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval", "compile"}:
            self.hits.append(f"{self.filename}:{node.lineno}:{node.func.id}")
        self.generic_visit(node)


def _module_uses_exec(path: Path) -> list[str]:
    finder = _ForbiddenCallFinder(path.name)
    finder.visit(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
    return finder.hits


class LhcSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FACTORY, "long-horizon-coding-factory")
        self.assertEqual(cv.GENERATOR, "grok-4.6")
        self.assertEqual(cv.PRESERVE_COMMIT, "813f93f1969c1c4421e5663492e9663739efa642")
        self.assertEqual(cv.SLICE_ID, "w4x-r4358")

    def test_one_hundred_thirty_four_catalog_sources(self):
        self.assertEqual(len(MILL_SOURCES), 134)
        self.assertEqual(len(catalog_sources()), 134)
        self.assertTrue(all(source.kind == cv.KIND_PAIRS for source in MILL_SOURCES))
        self.assertIn("lhc-mill-w4x-r4358", {source.mill_id for source in MILL_SOURCES})

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(
                path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path)
            )
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("lhc-mill-w4x-r4358.py"))
        self.assertTrue(is_vendor_filename("lhc_leftover_mill.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/lhc-mill-w4x-r4358.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "lhc"
        hits = []
        for name in (
            "catalog_ast.py",
            "catalog_ast_assign.py",
            "catalog_ast_calls.py",
            "catalog_ast_literals.py",
            "catalog_extract.py",
            "catalog_extract_fn_pair.py",
            "catalog_extract_pairs.py",
            "catalog_extract_plants.py",
            "catalog.py",
            "identity.py",
        ):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_extractor_reads_named_expand_pairs(self):
        extracted = extract_mill_catalog(
            _NAMED_SNIPPET, path="experiments/lhc-mill-w4x-r4358.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_PAIRS_NAMED)
        self.assertEqual(extracted["catalog_first"], 4358)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["n_plants"], 2)
        self.assertEqual(extracted["first_slug"], "pr-pnpm-peer-auto-install-strict")
        self.assertEqual(extracted["pairs"][0]["fail_plant"], "quay-bunlk")
        self.assertEqual(extracted["used_from"], 4163)

    def test_extractor_reads_named_plant_wrappers(self):
        extracted = extract_mill_catalog(
            _PLANTS_NAMED_SNIPPET, path="experiments/lhc-mill-w4bt-r4437.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_PLANTS_NAMED)
        self.assertEqual(extracted["n_plants"], 2)
        self.assertEqual(extracted["first_slug"], "pr-poetry-extras-marker-file-missing")
        self.assertEqual(extracted["pairs"][0]["success_key"], "poetry")
        self.assertEqual(extracted["pairs"][0]["fail_key"], "pdm")

    def test_extractor_reads_p_fn_kwargs(self):
        extracted = extract_mill_catalog(
            _P_FN_SNIPPET, path="experiments/lhc-mill-w4bu-r4453.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_PLANTS_P_FN)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "pr-hatch-env-scripts-extra-deps")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "pr-uv-sync-python-pin")

    def test_extractor_reads_mk_fn_positionals(self):
        extracted = extract_mill_catalog(
            _MK_FN_SNIPPET, path="experiments/lhc-mill-w4da-r4946.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_PLANTS_MK_FN)
        self.assertEqual(extracted["first_slug"], "pr-fiona-layer-crs")
        self.assertEqual(extracted["pairs"][0]["fail_plant"], "lock-pyog")

    def test_extractor_reads_fn_pair_appends(self):
        extracted = extract_mill_catalog(
            _FN_PAIR_SNIPPET, path="experiments/lhc-mill-lll-r4654.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_PAIRS_FN_PAIR)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["n_plants"], 2)
        self.assertEqual(extracted["first_slug"], "protobuf-reserved-field-tombstone")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "protobuf-json-name-leftover-alias")
        self.assertEqual(extracted["pairs"][0]["success_plant"], "protobuf-reserved")

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 134)
        self.assertEqual(CATALOG.n_pair_rows, 1326)
        self.assertEqual(CATALOG.n_plant_rows, 2652)
        self.assertEqual(CATALOG.slice, "w4x-r4358")
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        w4x = CATALOG.mills["lhc-mill-w4x-r4358"]
        self.assertEqual(w4x.n_rows, 15)
        self.assertEqual(w4x.n_plants, 30)
        self.assertEqual(w4x.catalog_first, 4358)
        self.assertEqual(w4x.shape, SHAPE_PAIRS_NAMED)
        self.assertEqual(w4x.first_slug, "pr-pnpm-peer-auto-install-strict")
        self.assertEqual(w4x.last_slug, "pr-airflow-mapped-task-expand-xcom")
        self.assertEqual(len(w4x.pairs), 15)
        self.assertEqual(w4x.pairs[0]["title"], "pnpm single React vs Bun workspace lock")
        self.assertEqual(w4x.pairs[0]["success_plant"], "lock-pnpmp")
        self.assertEqual(CATALOG.mills["lhc-mill-w4bt-r4437"].n_rows, 16)
        self.assertEqual(CATALOG.mills["lhc-mill-w4bt-r4437"].shape, SHAPE_PLANTS_NAMED)
        self.assertEqual(CATALOG.mills["lhc-mill-w4bu-r4453"].shape, SHAPE_PLANTS_P_FN)
        self.assertEqual(CATALOG.mills["lhc-mill-w4da-r4946"].first_slug, "pr-fiona-layer-crs")
        self.assertEqual(CATALOG.mills["lhc-mill-w4gs-r5713"].n_rows, 8)
        self.assertEqual(CATALOG.mills["lhc-mill-lll-r4654"].n_rows, 16)
        self.assertEqual(
            CATALOG.mills["lhc-mill-lll-r4654"].first_slug,
            "protobuf-reserved-field-tombstone",
        )
        self.assertFalse(CATALOG.mills["lhc-mill-w4gs-r5713"].pairs)


class LhcLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        mills = []
        for source in catalog_sources():
            text = _git_output("show", f"{cv.LEGACY_REF}:{source.path}")
            blob = _git_output("rev-parse", f"{cv.LEGACY_REF}:{source.path}").strip()
            self.assertEqual(blob, source.blob_sha, source.mill_id)
            live = extract_mill_catalog(text, path=source.path, blob_sha=source.blob_sha)
            committed = CATALOG.mills[source.mill_id]
            self.assertEqual(live["n_rows"], committed.n_rows, source.mill_id)
            self.assertEqual(live["n_plants"], committed.n_plants, source.mill_id)
            self.assertEqual(live["first_slug"], committed.first_slug, source.mill_id)
            self.assertEqual(live["last_slug"], committed.last_slug, source.mill_id)
            self.assertEqual(live["catalog_first"], committed.catalog_first, source.mill_id)
            self.assertEqual(len(live["sha256"]), 64, source.mill_id)
            self.assertEqual(live["path"], committed.path, source.mill_id)
            self.assertEqual(live["blob_sha"], committed.blob_sha, source.mill_id)
            self.assertEqual(live["shape"], committed.shape, source.mill_id)
            mills.append(mill_summary(live, include_pairs=is_slice_mill(source.mill_id)))
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
            self.assertEqual(list(dest.glob("lhc-mill*.py")), [])


if __name__ == "__main__":
    unittest.main()
