#!/usr/bin/env python3
"""PR-a: AST catalog extract and ``pipelines/amc`` skeleton (no vendored mills)."""

from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from amc.catalog import CATALOG  # noqa: E402
from amc.catalog_extract import (  # noqa: E402
    SHAPE_FAIL_SUCC,
    SHAPE_FS,
    SHAPE_L,
    SHAPE_LEFTOVER,
    SHAPE_P,
    SHAPE_PREFIX_NEW,
    SHAPE_TABLE_ZIP,
    catalog_document,
    catalog_json_path,
    compose_family,
    dumps_catalog,
    extract_companion_path,
    extract_mill_catalog,
    zip_table_pairs,
)
from amc.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from amc.sources import MILL_SOURCES, catalog_sources, loop_sources  # noqa: E402
from amc import vocabulary as av  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_FS_SNIPPET = """
FACTORY = "agent-memory-compaction-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 170
PAIRS = [
    (
        F(slug="zeigarnik-drops-unfinished-pin", leftover="incubation-timer", fail=True),
        S(slug="cowan-activated-ltm-keeps-pin", leftover="foa-capacity-later", fail=False),
    ),
]
"""

_FAIL_SUCC_SNIPPET = """
CATALOG_FIRST = 352
PAIRS = [
    (
        fail(slug="marksweep-gc-drops-pin", leftover="gray-stack-later"),
        succ(slug="marksweep-pin-kept", leftover="remark-queue-later"),
    ),
]
"""

_L_SNIPPET = """
CATALOG_FIRST = 592
PAIRS = [
    (
        L(slug="redis-volatile-ttl-leftover", leftover="redis-volatile-ttl-residue", is_fail=True),
        L(slug="memcached-slab-lru-leftover", leftover="memcached-slab-lru-residue", is_fail=False),
    ),
]
"""

_P_SNIPPET = """
CATALOG_FIRST = 688
PAIRS = [
    (
        P("mem0-entity-merge-leftover", "r8aa", "m0_em", "merge_live",
          "Mem0 entity-merge leftover", "mem0-entity-merge-residue", True),
        P("zep-fact-triple-leftover", "r8ab", "zp_ft", "triple_keep",
          "Zep fact-triple leftover", "zep-fact-triple-residue", False),
    ),
]
"""

_PREFIX_SNIPPET = """
CATALOG_FIRST = 280
NEW = [
    (
        F(slug="testing-effect-skip-drops-pin", leftover="roediger"),
        S(slug="retrieval-practice-keeps-pin", leftover="karpicke"),
    ),
]
PAIRS = list(_r229.PAIRS[:16]) + NEW
"""

_TABLE_SNIPPET = """
CATALOG_FIRST = 424
GC = [("shenandoah-satb", "Shenandoah SATB", "satb_marked")]
TOOL = [("cbor", "CBOR")]
NBACK = [("4", 4, "lag4")]
DOOR = [("airport", "airport gate", "gate")]
PAIRS = _build_pairs()
"""

_LEFTOVER_SNIPPET = """
FACTORY = "agent-memory-compaction-factory"
GEN = "grok-4.6"
MAX_ROUNDS = 16
CATALOG = [
    {
        "mod": "afxcom",
        "slug": "airflow-xcom-backend-leftover-vs-drop-task",
        "fail": "airflow-drop-xcom-backend-handoff",
        "token": "leftover_xcom_backend",
    },
]
"""


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", "origin/legacy-mill-lane:experiments/amc-mill-r170.py"],
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


class AmcSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[av.FAMILY_PREFIX], av.FACTORY)
        self.assertEqual(av.FACTORY, "agent-memory-compaction-factory")
        self.assertEqual(av.GENERATOR, "grok-4.6")
        self.assertEqual(av.PRESERVE_COMMIT, "bb0775859c86d4692112c4845790fa1623ab8abb")
        self.assertEqual(av.QUOTA_PER_ROUND, 2)
        self.assertEqual(av.SUCCESS_STEPS, 16)

    def test_twenty_three_sources_split_into_catalogs_and_loops(self):
        self.assertEqual(len(MILL_SOURCES), 23)
        self.assertEqual(len(catalog_sources()), 12)
        self.assertEqual(len(loop_sources()), 11)
        self.assertEqual({source.kind for source in loop_sources()}, {av.KIND_LOOP})
        self.assertEqual(
            {source.companion_mill_path for source in loop_sources()},
            {f"experiments/amc-mill-r{n}.py" for n in (
                170, 229, 280, 316, 352, 424, 592, 608, 650, 688, 704,
            )},
        )

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in av.FORBIDDEN_MILL_GLOBS:
            hits.extend(
                path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path)
            )
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("amc-mill-r170.py"))
        self.assertTrue(is_vendor_filename("amc-loop-r170.py"))
        self.assertTrue(is_vendor_filename("mill_amc_leftover_r688.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/amc-mill-r170.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "amc"
        hits = []
        for name in ("catalog_ast.py", "catalog_extract.py", "catalog.py", "identity.py"):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_extractor_reads_fs_kwargs(self):
        extracted = extract_mill_catalog(_FS_SNIPPET, path="experiments/amc-mill-r170.py")
        self.assertEqual(extracted["shape"], SHAPE_FS)
        self.assertEqual(extracted["catalog_first"], 170)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "zeigarnik-drops-unfinished-pin")
        self.assertEqual(extracted["pairs"][0]["success_slug"], "cowan-activated-ltm-keeps-pin")
        self.assertEqual(extracted["pairs"][0]["fail_leftover"], "incubation-timer")

    def test_extractor_reads_fail_succ_kwargs(self):
        extracted = extract_mill_catalog(
            _FAIL_SUCC_SNIPPET, path="experiments/amc-mill-r352.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_FAIL_SUCC)
        self.assertEqual(extracted["first_slug"], "marksweep-gc-drops-pin")
        self.assertEqual(extracted["pairs"][0]["success_leftover"], "remark-queue-later")

    def test_extractor_reads_l_kwargs(self):
        extracted = extract_mill_catalog(_L_SNIPPET, path="experiments/amc-mill-r592.py")
        self.assertEqual(extracted["shape"], SHAPE_L)
        self.assertEqual(extracted["first_slug"], "redis-volatile-ttl-leftover")
        self.assertEqual(extracted["pairs"][0]["success_slug"], "memcached-slab-lru-leftover")

    def test_extractor_reads_p_posargs(self):
        extracted = extract_mill_catalog(_P_SNIPPET, path="experiments/amc-mill-r688.py")
        self.assertEqual(extracted["shape"], SHAPE_P)
        self.assertEqual(extracted["first_slug"], "mem0-entity-merge-leftover")
        self.assertEqual(extracted["pairs"][0]["fail_leftover"], "mem0-entity-merge-residue")

    def test_extractor_reads_prefix_new_without_loading_r229(self):
        extracted = extract_mill_catalog(_PREFIX_SNIPPET, path="experiments/amc-mill-r280.py")
        self.assertEqual(extracted["shape"], SHAPE_PREFIX_NEW)
        self.assertEqual(extracted["n_prefix"], 16)
        self.assertEqual(extracted["n_new"], 1)
        self.assertEqual(extracted["n_rows"], 17)
        self.assertEqual(extracted["prefix_mill"], "amc-mill-r229")
        self.assertEqual(extracted["first_slug"], "testing-effect-skip-drops-pin")
        self.assertEqual(len(extracted["pairs"]), 1)

    def test_extractor_rebuilds_table_zip_slugs(self):
        extracted = extract_mill_catalog(_TABLE_SNIPPET, path="experiments/amc-mill-r424.py")
        self.assertEqual(extracted["shape"], SHAPE_TABLE_ZIP)
        self.assertEqual(extracted["n_rows"], 4)
        self.assertEqual(extracted["first_slug"], "shenandoah-satb-drops-pin")
        slugs = [row["fail_slug"] for row in extracted["pairs"]]
        self.assertEqual(
            slugs,
            [
                "shenandoah-satb-drops-pin",
                "tool-result-cbor-drops-pin",
                "nback-4-lure-drops-pin",
                "doorway-airport-drops-pin",
            ],
        )
        rebuilt = zip_table_pairs(
            [("shenandoah-satb", "Shenandoah SATB", "satb_marked")],
            [("cbor", "CBOR")],
            [("4", 4, "lag4")],
            [("airport", "airport gate", "gate")],
        )
        self.assertEqual(rebuilt, extracted["pairs"])

    def test_extractor_reads_leftover_dict_catalog(self):
        extracted = extract_mill_catalog(
            _LEFTOVER_SNIPPET, path="experiments/mill_amc_leftover_r688.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_LEFTOVER)
        self.assertEqual(extracted["kind"], av.KIND_LEFTOVER)
        self.assertEqual(extracted["catalog_first"], 688)
        self.assertEqual(extracted["max_rounds"], 16)
        self.assertEqual(
            extracted["first_slug"], "airflow-xcom-backend-leftover-vs-drop-task"
        )
        self.assertEqual(extracted["pairs"][0]["token"], "leftover_xcom_backend")

    def test_loop_mill_path_constant(self):
        source = (
            "REPO = Path(__file__).resolve().parents[1]\n"
            'MILL_PATH = REPO / "experiments/amc-mill-r170.py"\n'
        )
        self.assertEqual(
            extract_companion_path(source),
            "experiments/amc-mill-r170.py",
        )

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 12)
        self.assertEqual(CATALOG.n_pair_rows, 1401)
        self.assertEqual(CATALOG.preserve_commit, av.PRESERVE_COMMIT)
        self.assertEqual(CATALOG.mills["amc-mill-r170"].n_rows, 59)
        self.assertEqual(
            CATALOG.mills["amc-mill-r170"].first_slug, "zeigarnik-drops-unfinished-pin"
        )
        self.assertEqual(CATALOG.mills["amc-mill-r229"].n_rows, 51)
        r280 = CATALOG.mills["amc-mill-r280"]
        self.assertEqual(r280.shape, SHAPE_PREFIX_NEW)
        self.assertEqual(r280.n_rows, 36)
        self.assertEqual(r280.n_prefix, 16)
        self.assertEqual(r280.n_new, 20)
        self.assertEqual(r280.first_slug, "state-dependent-tag-stripped")
        self.assertEqual(r280.last_slug, "korsakoff-drops-recent-pin")
        self.assertEqual(len(r280.pairs), 36)
        self.assertEqual(r280.pairs[0]["fail_slug"], "state-dependent-tag-stripped")
        self.assertEqual(CATALOG.mills["amc-mill-r424"].n_rows, 999)
        self.assertEqual(
            CATALOG.mills["amc-mill-r424"].first_slug, "shenandoah-satb-drops-pin"
        )
        leftover = CATALOG.mills["mill_amc_leftover_r688"]
        self.assertEqual(leftover.n_rows, 16)
        self.assertEqual(leftover.max_rounds, 16)
        self.assertEqual(
            leftover.first_slug, "airflow-xcom-backend-leftover-vs-drop-task"
        )


class AmcLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        records = {}
        for source in catalog_sources():
            text = subprocess.check_output(
                ["git", "show", f"{av.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            blob = subprocess.check_output(
                ["git", "rev-parse", f"{av.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            ).strip()
            self.assertEqual(blob, source.blob_sha, source.mill_id)
            live = extract_mill_catalog(text, path=source.path, blob_sha=source.blob_sha)
            records[source.mill_id] = live
            committed = CATALOG.mills[source.mill_id]
            self.assertEqual(live["sha256"], committed.sha256, source.mill_id)
            self.assertEqual(live["shape"], committed.shape, source.mill_id)
            self.assertEqual(live["catalog_first"], committed.catalog_first, source.mill_id)
        mills = compose_family(records)
        by_id = {mill["mill_id"]: mill for mill in mills}
        for mill_id, committed in CATALOG.mills.items():
            live = by_id[mill_id]
            self.assertEqual(live["n_rows"], committed.n_rows, mill_id)
            self.assertEqual(live["first_slug"], committed.first_slug, mill_id)
            self.assertEqual(live["last_slug"], committed.last_slug, mill_id)
            self.assertEqual(len(live["pairs"]), committed.n_rows, mill_id)
        self.assertEqual(
            dumps_catalog(catalog_document(mills)),
            catalog_json_path().read_text(encoding="utf-8"),
        )

    def test_loop_scripts_name_companion_mills(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        for source in loop_sources():
            text = subprocess.check_output(
                ["git", "show", f"{av.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            self.assertEqual(
                extract_companion_path(text),
                source.companion_mill_path,
                source.mill_id,
            )


if __name__ == "__main__":
    unittest.main()
