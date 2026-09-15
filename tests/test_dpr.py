#!/usr/bin/env python3
"""PR-a: AST catalog extract and ``pipelines/dpr`` skeleton (no vendored mills)."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from dpr.catalog import CATALOG  # noqa: E402
from dpr.catalog_extract import (  # noqa: E402
    KIND_GEN,
    KIND_HOPPER,
    KIND_LOOP,
    KIND_PAIRS,
    KIND_PLANTS,
    DprExtractError,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    extract_call_path_constant,
    extract_joined_path_constant,
    extract_mill_catalog,
    is_hopper_path,
)
from dpr.sources import (  # noqa: E402
    MILL_SOURCES,
    catalog_sources,
    gen_sources,
    hopper_sources,
    loop_sources,
)
from dpr import vocabulary as dv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_PLANTS_SNIPPET = '''
FACTORY = "data-pipeline-repair-factory"
GEN = "grok-4.6"
MAX_ROUNDS = 16
CATALOG = [
    {
        "mod": "afxcom",
        "slug": "airflow-xcom-backend-leftover-vs-drop-task",
        "fail": "airflow-drop-xcom-backend-handoff",
        "stack": "Airflow leftover xcom_backend",
        "token": "leftover_xcom_backend",
        "wrong": "drop task",
        "wrong_key": "task",
        "test_ok": "test_xcom_not_task",
        "test_fail": "test_xcom_bind",
        "docs": "https://airflow.example/xcoms",
        "doc2": "https://airflow.example/logging",
        "handoff": "AF-XCOM-17",
        "domain_ok": "airflow-xcom-backend-leftover-vs-drop-task",
        "domain_fail": "airflow-drop-leftover-xcom-backend-bind",
        "first_patch": ("    return {'task': sid}", "    return {'task': None}"),
        "fix_patch": ("    return {'task': None}", "    return {'leftover_xcom_backend': sid}"),
        "src_obs": "Airflow leftover xcom_backend restores the same XCom store",
        "plan_ok": "Pass leftover_xcom_backend.",
        "plan_fail": "Handoff AF-XCOM-17.",
        "ban": "Not docker cache.",
    },
]
'''

_PAIRS_SNIPPET = '''
START = 2631
PAIRS = [
    (
        OK("lakefs-gc-uncommitted", "LakeFS GC vs disable LakeFS", "lakefs", "gc.yml",
           "gc.uncommitted", "off", "on", "lakefs.enabled=true", "lakefs.enabled=false",
           "LakeFS", "LF-01", "uncommitted", "sibling leftover", "symptom", "metric", 1, "lakefs"),
        FAIL("iceberg-rewrite", "Iceberg rewrite vs disable Iceberg", "iceberg", "rewrite.yml",
             "rewrite", "off", "on", "iceberg.enabled=true", "iceberg.enabled=false",
             "Iceberg", "IB-01", "rewrite", "LakeFS leftover", "lag", "lag_h", 2, "iceberg",
             "platform-iceberg"),
    ),
]
'''

_KEYWORD_SNIPPET = '''
PAIRS = [
    (
        OK(slug="xtable-sync", domain="apache-xtable", stack="XTable", seed="xtable-sync-off"),
        FAIL(slug="delta-uniform-ice", domain="delta-uniform", stack="Delta UniForm",
             seed="duniform-off", platform="platform-delta"),
    ),
]
'''


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", "origin/legacy-mill-lane:experiments/mill_dpr_leftover_r2631.py"],
            cwd=REPO,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


class DprSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[dv.FAMILY_PREFIX], dv.FACTORY)
        self.assertEqual(dv.FACTORY, "data-pipeline-repair-factory")

    def test_thirty_nine_sources_split_catalogs_loops_hoppers_and_gen(self):
        self.assertEqual(len(MILL_SOURCES), 39)
        self.assertEqual(len(catalog_sources()), 19)
        self.assertEqual(len(loop_sources()), 17)
        self.assertEqual(len(hopper_sources()), 2)
        self.assertEqual(len(gen_sources()), 1)
        self.assertEqual({source.kind for source in hopper_sources()}, {KIND_HOPPER})
        self.assertEqual({source.kind for source in gen_sources()}, {KIND_GEN})
        self.assertEqual({source.kind for source in loop_sources()}, {KIND_LOOP})
        self.assertTrue(all(source.lrd_mill_path for source in hopper_sources()))
        self.assertTrue(
            all(source.lrd_mill_path.startswith("experiments/lrd-") for source in hopper_sources())
        )

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in dv.FORBIDDEN_MILL_GLOBS:
            hits.extend(REPO.rglob(pattern))
        self.assertEqual(hits, [])

    def test_hopper_paths_are_detected_and_refused_by_the_extractor(self):
        self.assertTrue(is_hopper_path("experiments/dpr-lrd-hopper-leftover3.py"))
        self.assertTrue(is_hopper_path("experiments/dpr-lrd-hopper-leftover3b.py"))
        self.assertFalse(is_hopper_path("experiments/mill_dpr_leftover_r2631.py"))
        with self.assertRaises(DprExtractError) as ctx:
            extract_mill_catalog(_PLANTS_SNIPPET, path="experiments/dpr-lrd-hopper-leftover3.py")
        self.assertIn("lrd hopper", str(ctx.exception))

    def test_extractor_reads_leftover_catalog_dicts(self):
        extracted = extract_mill_catalog(
            _PLANTS_SNIPPET, path="experiments/mill_dpr_leftover_r2631.py"
        )
        self.assertEqual(extracted["kind"], KIND_PLANTS)
        self.assertEqual(extracted["catalog_first"], 2631)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["max_rounds"], 16)
        self.assertEqual(extracted["first_slug"], "airflow-xcom-backend-leftover-vs-drop-task")
        self.assertEqual(extracted["plants"][0]["token"], "leftover_xcom_backend")
        self.assertEqual(
            extracted["plants"][0]["first_patch"],
            ["    return {'task': sid}", "    return {'task': None}"],
        )

    def test_extractor_reads_positional_ok_fail_pairs(self):
        extracted = extract_mill_catalog(_PAIRS_SNIPPET, path="experiments/dpr-mill-r2631.py")
        self.assertEqual(extracted["kind"], KIND_PAIRS)
        self.assertEqual(extracted["catalog_first"], 2631)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "lakefs-gc-uncommitted")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "iceberg-rewrite")
        self.assertEqual(extracted["pairs"][0]["ok"]["ctor"], "OK")
        self.assertEqual(extracted["pairs"][0]["fail"]["ctor"], "FAIL")
        self.assertEqual(len(extracted["pairs"][0]["ok"]["args"]), 17)
        self.assertEqual(len(extracted["pairs"][0]["fail"]["args"]), 18)

    def test_extractor_reads_keyword_ok_fail_pairs(self):
        extracted = extract_mill_catalog(
            _KEYWORD_SNIPPET, path="experiments/dpr-mill-leftover3-r2475.py"
        )
        self.assertEqual(extracted["kind"], KIND_PAIRS)
        self.assertEqual(extracted["first_slug"], "xtable-sync")
        self.assertEqual(extracted["pairs"][0]["fail"]["kwargs"]["platform"], "platform-delta")

    def test_loop_and_hopper_path_constants(self):
        loop = (
            "REPO = Path(__file__).resolve().parents[1]\n"
            'MILL = REPO / "experiments/dpr-mill-leftover3-r2475.py"\n'
        )
        self.assertEqual(
            extract_joined_path_constant(loop, "MILL"),
            "experiments/dpr-mill-leftover3-r2475.py",
        )
        tmp = 'MILL = Path("/tmp/dpr_mill_r2631.py")\n'
        self.assertEqual(extract_call_path_constant(tmp, "MILL"), "/tmp/dpr_mill_r2631.py")
        hopper = (
            "REPO = Path(__file__).resolve().parents[1]\n"
            'DPR_MILL = REPO / "experiments/dpr-mill-leftover3-r2475.py"\n'
            'LRD_MILL = REPO / "experiments/lrd-mill-leftover3-r67.py"\n'
        )
        self.assertEqual(
            extract_joined_path_constant(hopper, "DPR_MILL"),
            "experiments/dpr-mill-leftover3-r2475.py",
        )
        self.assertEqual(
            extract_joined_path_constant(hopper, "LRD_MILL"),
            "experiments/lrd-mill-leftover3-r67.py",
        )

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 19)
        self.assertEqual(CATALOG.n_pair_rows, 727)
        self.assertEqual(CATALOG.n_plant_rows, 16)
        self.assertEqual(CATALOG.preserve_commit, dv.PRESERVE_COMMIT)
        leftover = CATALOG.mills["mill_dpr_leftover_r2631"]
        self.assertEqual(leftover.kind, KIND_PLANTS)
        self.assertEqual(leftover.n_rows, 16)
        self.assertEqual(leftover.first_slug, "airflow-xcom-backend-leftover-vs-drop-task")
        self.assertEqual(leftover.max_rounds, 16)
        self.assertNotIn("dpr-lrd-hopper-leftover3", CATALOG.mills)
        self.assertNotIn("dpr-lrd-hopper-leftover3b", CATALOG.mills)
        self.assertFalse(any("lrd" in mill.path for mill in CATALOG.mills.values()))
        self.assertFalse(any("hopper" in mill.path for mill in CATALOG.mills.values()))


@unittest.skipUnless(_legacy_available(), "origin/legacy-mill-lane is not fetched")
class DprLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        mills = []
        for source in catalog_sources():
            text = subprocess.check_output(
                ["git", "show", f"{dv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            blob = subprocess.check_output(
                ["git", "rev-parse", f"{dv.LEGACY_REF}:{source.path}"],
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
            mills.append(live)
        self.assertEqual(
            dumps_catalog(catalog_document(mills)),
            catalog_json_path().read_text(encoding="utf-8"),
        )

    def test_leftover3_loop_names_the_leftover3_mill(self):
        source = next(item for item in loop_sources() if item.mill_id == "dpr-loop-leftover3-r2475")
        text = subprocess.check_output(
            ["git", "show", f"{dv.LEGACY_REF}:{source.path}"],
            text=True,
            cwd=REPO,
        )
        self.assertEqual(
            extract_joined_path_constant(text, "MILL"),
            source.companion_mill_path,
        )

    def test_tmp_loops_name_the_matching_dpr_mill_copy(self):
        for source in loop_sources():
            if source.mill_id == "dpr-loop-leftover3-r2475":
                continue
            text = subprocess.check_output(
                ["git", "show", f"{dv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            tmp = extract_call_path_constant(text, "MILL")
            self.assertIsNotNone(tmp, source.mill_id)
            self.assertTrue(tmp.startswith("/tmp/dpr_mill_"), source.mill_id)
            stem = Path(tmp).stem
            self.assertIn(stem.replace("dpr_mill_", ""), source.companion_mill_path, source.mill_id)

    def test_hoppers_name_lrd_mills_and_stay_out_of_the_catalog(self):
        for source in hopper_sources():
            text = subprocess.check_output(
                ["git", "show", f"{dv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            self.assertEqual(
                extract_joined_path_constant(text, "DPR_MILL"),
                source.companion_mill_path,
            )
            self.assertEqual(
                extract_joined_path_constant(text, "LRD_MILL"),
                source.lrd_mill_path,
            )
            self.assertNotIn(source.mill_id, CATALOG.mills)
            with self.assertRaises(DprExtractError):
                extract_mill_catalog(text, path=source.path, blob_sha=source.blob_sha)


if __name__ == "__main__":
    unittest.main()
