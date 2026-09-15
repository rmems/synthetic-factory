#!/usr/bin/env python3
"""PR-a: AST catalog extract and ``pipelines/mdb`` skeleton (no vendored mills)."""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from mdb.catalog import CATALOG  # noqa: E402
from mdb.catalog_extract import (  # noqa: E402
    SHAPE_LITERAL,
    SHAPE_P_CTOR,
    SHAPE_R_CTOR,
    SHAPE_RAW,
    SHAPE_SLUGS,
    SHAPE_TOOLS,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    extract_companion_path,
    extract_mill_catalog,
    is_slice_mill,
    mill_summary,
)
from mdb.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from mdb.sources import MILL_SOURCES, catalog_sources, gen_sources, loop_sources  # noqa: E402
from mdb import vocabulary as cv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_R709_SNIPPET = """
FACTORY = "monorepo-dep-bump-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 709
PAIRS: list[tuple[dict, dict]] = [
    (
        {"slug": "keep-a", "plant": "kestrel", "fail": False},
        {"slug": "keep-a-fail", "plant": "merlin", "fail": True},
    ),
    (
        {"slug": "keep-b", "plant": "hobby", "fail": False},
        {"slug": "keep-b-fail", "plant": "saker", "fail": True},
    ),
]
"""

_P_CTOR_SNIPPET = """
CATALOG_FIRST = 776
PAIRS: list[tuple[dict, dict]] = [
    (
        P("ansible-galaxy-leftover-k8score", "alpha", "surface", "pkg", "1", "2", False,
          "sot", "nested", "so", "sn", "no", "nn", "ao", "an", "brk", "tool", "test", "ws", "call"),
        P("argo-wf-leftover-retry", "beta", "surface", "pkg", "1", "2", True,
          "sot", "nested", "so", "sn", "no", "nn", "ao", "an", "brk", "tool", "test", "ws", "call"),
    ),
]
"""

_TOOLS_SNIPPET = """
CATALOG_FIRST = 918
TOOLS: list[tuple] = [
    ("openmc-xml-leftover-batches", "surface", "pkg", "old", "new"),
    ("graphite-conf-leftover-schema", "surface", "pkg", "old", "new"),
]
"""

_RAW_SNIPPET = """
CATALOG_FIRST = 1351
RAW: list[tuple] = [
    ("ffmpeg-ffpreset-leftover-codec", "surface", "pkg", "old", "new", "pin",
     "no", "nn", "ao", "an", "brk", "ext"),
    ("hydra-py-leftover-compose", "surface", "pkg", "old", "new", "pin",
     "no", "nn", "ao", "an", "brk", "ext"),
]
TOOLS = [expand(r) for r in RAW]
"""

_R_CTOR_SNIPPET = """
CATALOG_FIRST = 1454
RAW: list[tuple] = [
    R("wezterm", "toml", "termgpu", "WezTerm", "1", "2", "pin.toml",
      "no", "nn", "ao", "an", "brk"),
    R("just", "justfile", "dotenv", "just", "1", "2", "pin.justfile",
      "no", "nn", "ao", "an", "brk"),
]
"""

_SLUGS_SNIPPET = """
CATALOG_FIRST = 1534
SLUGS = [
    "jellyfin-xml-leftover-transcode",
    "beszel-yml-leftover-agent",
]
"""


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", "origin/legacy-mill-lane:experiments/mdb-mill-r709.py"],
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


class MdbSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FACTORY, "monorepo-dep-bump-factory")
        self.assertEqual(cv.GENERATOR, "grok-4.6")
        self.assertEqual(cv.PRESERVE_COMMIT, "f769a8c09e45960ca7a3b7d600cbb2a481a67516")

    def test_forty_one_sources_split_into_mills_loops_and_gens(self):
        self.assertEqual(len(MILL_SOURCES), 41)
        self.assertEqual(len(catalog_sources()), 20)
        self.assertEqual(len(loop_sources()), 20)
        self.assertEqual(len(gen_sources()), 1)
        self.assertEqual(
            {source.companion_mill_path for source in loop_sources()},
            {
                "experiments/mdb-mill-r709.py",
                "experiments/mdb-mill-r746.py",
                "experiments/mdb-mill-r762.py",
                "experiments/mdb-mill-r840.py",
                "experiments/mdb-mill-r918.py",
                "experiments/mdb-mill-r961.py",
                "experiments/mdb-mill-r1068.py",
                "experiments/mdb-mill-r1148.py",
                "experiments/mdb-mill-r1208.py",
                "experiments/mdb-mill-r1351.py",
                "experiments/mdb-mill-r1407.py",
                "experiments/mdb-mill-r1454.py",
                "experiments/mdb-mill-r1534.py",
                "experiments/mdb-mill-r1614.py",
                "experiments/mdb-mill-r1694.py",
                "experiments/mdb-mill-r1774.py",
                "experiments/mdb-mill-r1854.py",
                "experiments/mdb-mill-r1934.py",
            },
        )
        self.assertEqual(
            next(s.companion_mill_path for s in loop_sources() if s.mill_id == "mdb-loop-r1084"),
            "experiments/mdb-mill-r1148.py",
        )
        self.assertEqual(
            next(s.companion_mill_path for s in loop_sources() if s.mill_id == "mdb-loop-r776"),
            "experiments/mdb-mill-r840.py",
        )

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path))
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("mdb-mill-r709.py"))
        self.assertTrue(is_vendor_filename("mdb-loop-r709.py"))
        self.assertTrue(is_vendor_filename("_gen_mdb_r1208.py"))
        self.assertTrue(is_vendor_filename("mdb-hop-loop.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/mdb-mill-r709.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "mdb"
        hits = []
        for name in ("catalog_ast.py", "catalog_extract.py", "catalog.py", "identity.py"):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_extractor_reads_literal_pairs(self):
        extracted = extract_mill_catalog(_R709_SNIPPET, path="experiments/mdb-mill-r709.py")
        self.assertEqual(extracted["shape"], SHAPE_LITERAL)
        self.assertEqual(extracted["catalog_first"], 709)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "keep-a")
        self.assertEqual(extracted["last_slug"], "keep-b")
        self.assertEqual(extracted["pairs"][0]["fail_plant"], "merlin")
        self.assertTrue(extracted["pairs"][0]["fail"])

    def test_extractor_reads_p_ctor_args(self):
        extracted = extract_mill_catalog(_P_CTOR_SNIPPET, path="experiments/mdb-mill-r776.py")
        self.assertEqual(extracted["shape"], SHAPE_P_CTOR)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "ansible-galaxy-leftover-k8score")
        self.assertEqual(extracted["pairs"][0]["success_plant"], "alpha")
        self.assertTrue(extracted["pairs"][0]["fail"])

    def test_extractor_reads_tools_table(self):
        extracted = extract_mill_catalog(_TOOLS_SNIPPET, path="experiments/mdb-mill-r918.py")
        self.assertEqual(extracted["shape"], SHAPE_TOOLS)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "openmc-xml-leftover-batches")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "graphite-conf-leftover-schema")

    def test_extractor_reads_raw_tuples(self):
        extracted = extract_mill_catalog(_RAW_SNIPPET, path="experiments/mdb-mill-r1351.py")
        self.assertEqual(extracted["shape"], SHAPE_RAW)
        self.assertEqual(extracted["first_slug"], "ffmpeg-ffpreset-leftover-codec")
        self.assertEqual(extracted["last_slug"], "ffmpeg-ffpreset-leftover-codec")

    def test_extractor_rebuilds_r_ctor_slugs(self):
        extracted = extract_mill_catalog(_R_CTOR_SNIPPET, path="experiments/mdb-mill-r1454.py")
        self.assertEqual(extracted["shape"], SHAPE_R_CTOR)
        self.assertEqual(extracted["first_slug"], "wezterm-toml-leftover-termgpu")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "just-justfile-leftover-dotenv")

    def test_extractor_reads_slugs_list(self):
        extracted = extract_mill_catalog(_SLUGS_SNIPPET, path="experiments/mdb-mill-r1534.py")
        self.assertEqual(extracted["shape"], SHAPE_SLUGS)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "jellyfin-xml-leftover-transcode")

    def test_loop_mill_path_constant(self):
        source = (
            "ROOT = Path(__file__).resolve().parents[1]\n"
            'MILL = ROOT / "experiments" / "mdb-mill-r709.py"\n'
        )
        self.assertEqual(extract_companion_path(source), "experiments/mdb-mill-r709.py")
        hop = 'MDB_MILL = ROOT / "experiments" / "mdb-mill-r840.py"\n'
        self.assertEqual(extract_companion_path(hop), "experiments/mdb-mill-r840.py")

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 20)
        self.assertEqual(CATALOG.n_pair_rows, 1321)
        self.assertEqual(CATALOG.slice, "r709")
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        r709 = CATALOG.mills["mdb-mill-r709"]
        self.assertEqual(r709.n_rows, 37)
        self.assertEqual(r709.catalog_first, 709)
        self.assertEqual(r709.first_slug, "bazel-bzlmod-vs-workspace-protobuf")
        self.assertEqual(r709.last_slug, "argocd-appproj-leftover-sourcehydrate")
        self.assertEqual(len(r709.pairs), 37)
        self.assertEqual(r709.pairs[0]["success_plant"], "kestrel")
        self.assertTrue(r709.pairs[0]["fail"])
        self.assertEqual(CATALOG.mills["mdb-mill-r961"].catalog_first, 977)
        self.assertEqual(CATALOG.mills["mdb-mill-r918"].n_rows, 150)
        self.assertEqual(CATALOG.mills["mdb-mill-r1934"].n_rows, 80)
        self.assertFalse(CATALOG.mills["mdb-mill-r1934"].pairs)


class MdbLegacyExtractTests(unittest.TestCase):
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
            mills.append(mill_summary(live, include_pairs=is_slice_mill(source.mill_id)))
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
            self.assertEqual(list(dest.glob("mdb-mill*.py")), [])


if __name__ == "__main__":
    unittest.main()
