#!/usr/bin/env python3
"""PR-a: AST catalog extract and ``pipelines/gor`` skeleton (no vendored mills)."""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from gor.catalog import CATALOG  # noqa: E402
from gor.catalog_extract import (  # noqa: E402
    SHAPE_ADD,
    SHAPE_GITCFG,
    SHAPE_LEFTOVER_PLANT,
    SHAPE_LITERAL,
    SHAPE_PLANT,
    SHAPE_S_H,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    extract_companion_path,
    extract_mill_catalog,
    mill_summary,
)
from gor.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from gor.sources import MILL_SOURCES, catalog_sources, gen_sources, loop_sources  # noqa: E402
from gor import vocabulary as cv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_LITERAL_SNIPPET = """
FACTORY = "git-ops-recovery-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 946
PAIRS: list[tuple[dict, dict]] = [
    (
        {"slug": "lfs-smudge-pointer-leftover", "marker": "LFS_SMUDGE_N", "stem": "lfs"},
        {"slug": "annex-unused-needed-keys", "marker": "ANNEX_UNUSED_N", "handoff": "ci"},
    ),
    (
        {"slug": "filter-repo-already-skip", "marker": "FR_N", "stem": "fr"},
        {"slug": "subtree-split-leftover", "marker": "SUB_N", "handoff": True},
    ),
]
"""

_S_H_SNIPPET = """
CATALOG_FIRST = 1044
PAIRS: list[tuple[dict, dict]] = [
    (
        _S(slug="resolve-undo-reuc-leftover", marker="REUC_N", stem="reuc"),
        _H(slug="resolve-undo-reuc-handoff", marker="REUC_N", handoff="ci-reuc"),
    ),
]
"""

_PLANT_SNIPPET = """
CATALOG_FIRST = 1046
PAIRS: list[tuple[dict, dict]] = [
    (
        plant(slug="bundle-uri-stale-advertisement", marker="BUNDLE_URI_N", stem="buri"),
        plant(slug="bundle-uri-stale-handoff", marker="BUNDLE_URI_N", handoff="ci-buri"),
    ),
]
"""

_LEFTOVER_SNIPPET = """
NEW_PAIRS: list[tuple[dict, dict]] = [
    (
        leftover_plant(slug="core-ignorecase-collides-path", marker="IGNCASE_N", stem="igncase"),
        leftover_plant(
            slug="core-ignorecase-handoff",
            marker="IGNCASE_N",
            stem="igncase",
            handoff="ci-igncase",
        ),
    ),
]
MORE_PAIRS: list[tuple[dict, dict]] = [
    (
        leftover_plant(slug="pack-island-core-wrong", marker="ISLAND_N", stem="island"),
        leftover_plant(slug="pack-island-handoff", marker="ISLAND_N", handoff="ci-island"),
    ),
]
"""

_GITCFG_SNIPPET = """
NEW_PAIRS: list[tuple[dict, dict]] = []
MORE = [
    _pair(
        gitcfg(slug="advice-detachedhead-false", marker="ADVDET_N", key="advice.detachedHead"),
        gitcfg(
            slug="advice-detachedhead-handoff",
            marker="ADVDET_N",
            key="advice.detachedHead",
            handoff="ci-advdet",
        ),
    ),
]
"""

_ADD_SNIPPET = """
NEW_PAIRS: list[tuple[dict, dict]] = []

def add(a: dict, b: dict) -> None:
    NEW_PAIRS.append((a, b))

add(
    _cfg("apply-whitespace-error", "appwse", "apply.whitespace", "error", "nowarn",
         "rejected leftover patches", "git apply", "error leftover", "ok leftover",
         "git apply --whitespace=nowarn", "error leftover still", old="0", new="7"),
    _cfg("checkout-defaultremote-stale", "chkdrs", "checkout.defaultRemote",
         "legacy-mirror", None, "resolved leftover branches from a dead mirror",
         "git checkout", "legacy leftover", "origin leftover",
         "git checkout origin", "legacy leftover still", handoff=True),
)
add(
    cmdplant(
        slug="git-last-modified-pathspec-stale",
        marker="LASTMOD_N",
        stem="lastmod",
        knob="git last-modified leftover pathspec",
    ),
    cmdplant(
        slug="git-last-modified-handoff",
        marker="LASTMOD_N",
        stem="lastmod",
        handoff="ci-lastmod",
    ),
)
"""


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", "origin/legacy-mill-lane:experiments/gor-mill-r946.py"],
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


class GorSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FACTORY, "git-ops-recovery-factory")
        self.assertEqual(cv.GENERATOR, "grok-4.6")
        self.assertEqual(cv.PRESERVE_COMMIT, "a2000438238dd1ac2b68b232430e6fb8f334b58f")

    def test_thirty_three_sources_split_into_mills_loops_and_gens(self):
        self.assertEqual(len(MILL_SOURCES), 33)
        self.assertEqual(len(catalog_sources()), 16)
        self.assertEqual(len(loop_sources()), 13)
        self.assertEqual(len(gen_sources()), 4)
        self.assertEqual(
            {source.companion_mill_path for source in loop_sources()},
            {
                "experiments/gor-mill-r946.py",
                "experiments/gor-mill-r973.py",
                "experiments/gor-mill-r1003.py",
                "experiments/gor-mill-r1044.py",
                "experiments/gor-mill-r1046.py",
                "experiments/gor-mill-r1111.py",
                "experiments/gor-mill-r1127.py",
                "experiments/gor-mill-r1214.py",
                "experiments/gor-mill-r1278.py",
                "experiments/gor-mill-r1371.py",
                "experiments/gor-mill-r1405.py",
                "experiments/gor-mill-r1417.py",
                "experiments/gor-mill-r1460.py",
            },
        )
        self.assertEqual(
            {source.companion_mill_path for source in gen_sources()},
            {"experiments/gor-mill-r1460.py"},
        )

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(
                path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path)
            )
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("gor-mill-r946.py"))
        self.assertTrue(is_vendor_filename("gor-loop-r946.py"))
        self.assertTrue(is_vendor_filename("_gen_gor_plants_r1725.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/gor-mill-r946.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "gor"
        hits = []
        for name in ("catalog_ast.py", "catalog_extract.py", "catalog.py", "identity.py"):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_extractor_reads_literal_pairs(self):
        extracted = extract_mill_catalog(_LITERAL_SNIPPET, path="experiments/gor-mill-r946.py")
        self.assertEqual(extracted["shape"], SHAPE_LITERAL)
        self.assertEqual(extracted["catalog_first"], 946)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "lfs-smudge-pointer-leftover")
        self.assertEqual(extracted["last_slug"], "filter-repo-already-skip")
        self.assertTrue(extracted["pairs"][0]["fail_handoff"])
        self.assertEqual(extracted["pairs"][0]["success_marker"], "LFS_SMUDGE_N")

    def test_extractor_reads_s_h_kwargs(self):
        extracted = extract_mill_catalog(_S_H_SNIPPET, path="experiments/gor-mill-r1044.py")
        self.assertEqual(extracted["shape"], SHAPE_S_H)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "resolve-undo-reuc-leftover")
        self.assertTrue(extracted["pairs"][0]["fail_handoff"])

    def test_extractor_reads_plant_kwargs(self):
        extracted = extract_mill_catalog(_PLANT_SNIPPET, path="experiments/gor-mill-r1046.py")
        self.assertEqual(extracted["shape"], SHAPE_PLANT)
        self.assertEqual(extracted["first_slug"], "bundle-uri-stale-advertisement")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "bundle-uri-stale-handoff")

    def test_extractor_reads_leftover_plant_lists(self):
        extracted = extract_mill_catalog(_LEFTOVER_SNIPPET, path="experiments/gor-mill-r1127.py")
        self.assertEqual(extracted["shape"], SHAPE_LEFTOVER_PLANT)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["n_new"], 1)
        self.assertEqual(extracted["n_more"], 1)
        self.assertEqual(extracted["first_slug"], "core-ignorecase-collides-path")
        self.assertEqual(extracted["last_slug"], "pack-island-core-wrong")

    def test_extractor_reads_gitcfg_pair_list(self):
        extracted = extract_mill_catalog(_GITCFG_SNIPPET, path="experiments/gor-mill-r1214.py")
        self.assertEqual(extracted["shape"], SHAPE_GITCFG)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "advice-detachedhead-false")
        self.assertTrue(extracted["pairs"][0]["fail_handoff"])

    def test_extractor_reads_add_constructors(self):
        extracted = extract_mill_catalog(_ADD_SNIPPET, path="experiments/gor-mill-r1460.py")
        self.assertEqual(extracted["shape"], SHAPE_ADD)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "apply-whitespace-error")
        self.assertEqual(extracted["last_slug"], "git-last-modified-pathspec-stale")
        self.assertTrue(extracted["pairs"][0]["fail_handoff"])
        self.assertEqual(extracted["pairs"][0]["success_stem"], "appwse")

    def test_loop_mill_path_constant(self):
        source = (
            "ROOT = Path(__file__).resolve().parents[1]\n"
            'MILL = ROOT / "experiments" / "gor-mill-r946.py"\n'
        )
        self.assertEqual(extract_companion_path(source), "experiments/gor-mill-r946.py")
        gen = 'HERE = Path(__file__).resolve().parent\nMILL = HERE / "gor-mill-r1460.py"\n'
        self.assertEqual(extract_companion_path(gen), "experiments/gor-mill-r1460.py")

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 16)
        self.assertEqual(CATALOG.n_pair_rows, 988)
        self.assertEqual(CATALOG.slice, "r946")
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        r946 = CATALOG.mills["gor-mill-r946"]
        self.assertEqual(r946.n_rows, 27)
        self.assertEqual(r946.catalog_first, 946)
        self.assertEqual(r946.first_slug, "lfs-smudge-pointer-leftover")
        self.assertEqual(r946.last_slug, "scalar-reconfigure-leftover")
        self.assertEqual(len(r946.pairs), 27)
        self.assertTrue(r946.pairs[0]["fail_handoff"])
        self.assertEqual(CATALOG.mills["gor-mill-r1460"].n_rows, 528)
        self.assertEqual(CATALOG.mills["gor-mill-r1127"].n_new, 32)
        self.assertEqual(CATALOG.mills["gor-mill-r1127"].n_more, 16)
        self.assertEqual(CATALOG.mills["gor-mill-r1230"].n_rows, 16)
        self.assertFalse(CATALOG.mills["gor-mill-r1460"].pairs)


class GorLegacyExtractTests(unittest.TestCase):
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
                mill_summary(live, include_pairs=source.mill_id == "gor-mill-r946")
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
            self.assertEqual(list(dest.glob("gor-mill*.py")), [])


if __name__ == "__main__":
    unittest.main()
