#!/usr/bin/env python3
"""PR-a: AST catalog extract and ``pipelines/cst`` skeleton (no vendored mills)."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from cst.catalog import CATALOG  # noqa: E402
from cst.catalog_extract import (  # noqa: E402
    KIND_LOOP,
    KIND_PAIRS,
    KIND_PLANTS,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    extract_catalog_namespace,
    extract_joined_path_constant,
    extract_mill_catalog,
)
from cst.sources import MILL_SOURCES, catalog_sources, loop_sources  # noqa: E402
from cst import vocabulary as cv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_PAIRS_SNIPPET = '''
CATALOG_FIRST = 1414
PAIRS: list[tuple] = [
    ("Redis CLIENT TRACKING", "redis-tracking-invalidation-leftover",
     "redis-tracking-bcast-handoff", "flock-rtrack", "src/a.go",
     "tests/test_a.py", "CLIENT TRACKING ON REDIRECT", "drop CLIENT TRACKING on miss",
     "tracking leftover + wait + do(key)", 31, "residual", "sibling",
     "src/b.go", "tests/test_b.py", "invalidations"),
]
'''

_PLANTS_SNIPPET = '''
GEN = "grok-4.6"
FAC = "cache-stampede-factory"
PLANTS = [
    {
        "slug_ok": "meili-filterable-leftover",
        "slug_bad": "quickwit-split-handoff",
        "ok": dict(plant="flock-meili", seed=28, product="Meilisearch"),
        "bad": dict(plant="flock-qw", seed=14, product="Quickwit"),
    },
]
'''

_CTOR_SNIPPET = '''
def plant(slug_ok, slug_bad, ok_kw, bad_kw):
    return {"slug_ok": slug_ok, "slug_bad": slug_bad, "ok": ok_kw, "bad": bad_kw}

def ok(plant_id, seed):
    return dict(plant=plant_id, seed=seed)

def bad(plant_id, seed):
    return dict(plant=plant_id, seed=seed)

MAX_ROUNDS = 16
PLANTS = [
    plant("redis-tracking-n0-leftover", "redis-tracking-optin-handoff",
          ok("flock-rtrack", 31), bad("flock-roptin", 15)),
]
'''


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", "origin/legacy-mill-lane:experiments/cst-mill-r1414.py"],
            cwd=REPO,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


class CstSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FACTORY, "cache-stampede-factory")

    def test_twenty_one_sources_split_into_catalogs_and_loops(self):
        self.assertEqual(len(MILL_SOURCES), 21)
        self.assertEqual(len(catalog_sources()), 19)
        self.assertEqual(len(loop_sources()), 2)
        self.assertEqual({source.kind for source in loop_sources()}, {KIND_LOOP})
        self.assertEqual(
            {source.companion_mill_path for source in loop_sources()},
            {"experiments/cst-mill-r1414.py", "experiments/cst-mill-r2310.py"},
        )

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(REPO.rglob(pattern))
        self.assertEqual(hits, [])

    def test_extractor_reads_pairs_annassign(self):
        extracted = extract_mill_catalog(_PAIRS_SNIPPET, path="experiments/cst-mill-r1414.py")
        self.assertEqual(extracted["kind"], KIND_PAIRS)
        self.assertEqual(extracted["catalog_first"], 1414)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["pair_arity"], 15)
        self.assertEqual(extracted["first_slug"], "redis-tracking-invalidation-leftover")
        self.assertEqual(extracted["pairs"][0][3], "flock-rtrack")

    def test_extractor_reads_plants_dict_calls(self):
        namespace = extract_catalog_namespace(_PLANTS_SNIPPET)
        self.assertEqual(namespace["GEN"], cv.GENERATOR)
        extracted = extract_mill_catalog(
            _PLANTS_SNIPPET, path="experiments/cst_r1369_leftover_mill.py"
        )
        self.assertEqual(extracted["kind"], KIND_PLANTS)
        self.assertEqual(extracted["catalog_first"], 1369)
        self.assertEqual(extracted["plants"][0]["ok"]["plant"], "flock-meili")

    def test_extractor_reads_plant_ok_bad_constructors(self):
        extracted = extract_mill_catalog(
            _CTOR_SNIPPET, path="experiments/cst_r1405_leftover3_mill.py"
        )
        self.assertEqual(extracted["max_rounds"], 16)
        self.assertEqual(extracted["first_slug"], "redis-tracking-n0-leftover")
        self.assertEqual(extracted["plants"][0]["bad"]["plant"], "flock-roptin")

    def test_loop_mill_path_constant(self):
        source = (
            "REPO = Path(__file__).resolve().parents[1]\n"
            'MILL_PATH = REPO / "experiments/cst-mill-r1414.py"\n'
        )
        self.assertEqual(
            extract_joined_path_constant(source, "MILL_PATH"),
            "experiments/cst-mill-r1414.py",
        )

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 19)
        self.assertEqual(CATALOG.n_pair_rows, 1026)
        self.assertEqual(CATALOG.n_plant_rows, 48)
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        self.assertEqual(CATALOG.mills["cst-mill-r2430"].pair_arity, 18)
        self.assertEqual(CATALOG.mills["cst-mill-r1414"].first_slug, "redis-tracking-invalidation-leftover")
        self.assertEqual(CATALOG.mills["cst_r1405_leftover3_mill"].first_slug, "redis-tracking-n0-leftover")


@unittest.skipUnless(_legacy_available(), "origin/legacy-mill-lane is not fetched")
class CstLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
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
            mills.append(live)
        self.assertEqual(
            dumps_catalog(catalog_document(mills)),
            catalog_json_path().read_text(encoding="utf-8"),
        )

    def test_loop_scripts_name_companion_mills(self):
        for source in loop_sources():
            text = subprocess.check_output(
                ["git", "show", f"{cv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            self.assertEqual(
                extract_joined_path_constant(text, "MILL_PATH"),
                source.companion_mill_path,
                source.mill_id,
            )


if __name__ == "__main__":
    unittest.main()
