#!/usr/bin/env python3
"""AST catalog extract and ``pipelines/evh`` skeleton (no vendored mills)."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from evh.catalog import CATALOG  # noqa: E402
from evh.catalog_extract import (  # noqa: E402
    PAIR_IDENTITY_KEYS,
    PAIR_ROW_KEYS,
    SHAPE_ADD_TABLES,
    SHAPE_FSTRING,
    SHAPE_PARAM,
    SHAPE_RAW,
    catalog_document,
    catalog_json_path,
    deferred_rows_from_extract,
    dumps_catalog,
    extract_companion_path,
    extract_plant_catalog,
    mill_summary,
    pairs_jsonl_path,
)
from evh.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from evh.leftover_plants import load_leftover_plants  # noqa: E402
from evh.leftover_plants_b import load_leftover_plants_b  # noqa: E402
from evh.pairs import load_pairs  # noqa: E402
from evh.plants_extract import (  # noqa: E402
    extract_leftover_plant_pairs,
    leftover_plants_b_jsonl_path,
    leftover_plants_jsonl_path,
)
from evh.sources import MILL_SOURCES, catalog_sources, loop_sources, source_by_id  # noqa: E402
from evh import vocabulary as cv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_R801_SNIPPET = """
PLANTED_OK = [
    "restock-void", "gift-void", "tax-void", "seat-void", "dual-void",
    "promo-void", "cancel-void", "after-void", "warranty-void", "hold-void",
]
PLANTED_BAD = [
    "flash-cut", "loyalty-cut", "membership-cut", "chargeback-cut", "rain-cut",
    "bundle-cut", "sla-cut", "pickup-cut", "inventory-cut", "window-cut",
]
OUT = MILL / "mill_plants_w.py"

def catalog():
    rows = []
    def add(*a):
        rows.append(a)
    mets = [
        ("ansrel-strict-canary-stale", "cwansstr-eval",
         "AnswerRelevancyMetric(strict_mode=False, threshold=0.15)",
         "AnswerRelevancyMetric(strict_mode=False, threshold=0.28)",
         "AnswerRelevancyMetric(strict_mode=True, threshold=0.5)",
         "halluc-strict-canary-stale", "cwhalstr-eval",
         "HallucinationMetric(strict_mode=False, threshold=0.15)",
         "HallucinationMetric(strict_mode=False, threshold=0.28)",
         "HallucinationMetric(strict_mode=True, threshold=0.5)"),
    ]
    for m in mets:
        add(m[0], m[1], m[5], m[6], m[2], m[7], m[3], m[8], m[4], m[9], "metric")
    return rows

def with_plants(rows):
    out = []
    for i, r in enumerate(rows):
        n = 59 + i // 10
        out.append(r)
    return out
"""

_RAW_SNIPPET = """
POK = [
    "restock-void", "gift-void", "tax-void", "seat-void", "dual-void",
    "promo-void", "cancel-void", "after-void", "warranty-void", "hold-void",
]
PBAD = [
    "flash-cut", "loyalty-cut", "membership-cut", "chargeback-cut", "rain-cut",
    "bundle-cut", "sla-cut", "pickup-cut", "inventory-cut", "window-cut",
]
OUT = MILL / "mill_plants_x.py"
RAW = [
    ("ansrel-minscore-hold-stale", "xansmin-eval",
     "AnswerRelevancyMetric(minimum_score=0.0)",
     "AnswerRelevancyMetric(minimum_score=0.2)",
     "AnswerRelevancyMetric(threshold=0.5, strict_mode=True)",
     "halluc-minscore-hold-stale", "xhalmin-eval",
     "HallucinationMetric(minimum_score=0.0)",
     "HallucinationMetric(minimum_score=0.2)",
     "HallucinationMetric(threshold=0.5, strict_mode=True)", "metric"),
]

def main():
    for i, raw in enumerate(RAW):
        n = 72 + i // 10
        PAIRS.append(eval_pair(*raw[:12], i + 446, raw[12]))
"""

_FSTRING_SNIPPET = """
POK = [
    "restock-void", "gift-void", "tax-void", "seat-void", "dual-void",
    "promo-void", "cancel-void", "after-void", "warranty-void", "hold-void",
]
PBAD = [
    "flash-cut", "loyalty-cut", "membership-cut", "chargeback-cut", "rain-cut",
    "bundle-cut", "sla-cut", "pickup-cut", "inventory-cut", "window-cut",
]
METS = [
    ("AnswerRelevancyMetric", "ansrel", "HallucinationMetric", "halluc"),
]

def add_row(rows, *a):
    rows.append(a)

def catalog():
    rows = []
    for a, sa, b, sb in METS:
        add_row(
            rows,
            f"{sa}-embed-hub-stale", f"aa{sa}emb-eval",
            f"{sb}-embed-hub-stale", f"aa{sb}emb-eval",
            f"{a}(embedder='hub-embed', threshold=0.17)",
            f"{b}(embedder='hub-embed', threshold=0.17)",
            f"{a}(embedder='hub-dev-embed', threshold=0.27)",
            f"{b}(embedder='hub-dev-embed', threshold=0.27)",
            f"{a}(embedder=EMBED_LOCK, threshold=0.5)",
            f"{b}(embedder=EMBED_LOCK, threshold=0.5)",
            "metric",
        )
    return rows

def main():
    dest = MILL / "mill_plants_aa.py"
    n = 96 + i // 10
    PAIRS.append(eval_pair(*row[:12], i + 680, row[12]))
"""

_PARAM_SNIPPET = """
POK = [
    "restock-void", "gift-void", "tax-void", "seat-void", "dual-void",
    "promo-void", "cancel-void", "after-void", "warranty-void", "hold-void",
]
PBAD = [
    "flash-cut", "loyalty-cut", "membership-cut", "chargeback-cut", "rain-cut",
    "bundle-cut", "sla-cut", "pickup-cut", "inventory-cut", "window-cut",
]
METS = [
    ("AnswerRelevancyMetric", "ansrel", "HallucinationMetric", "halluc"),
]

def add_row(rows, *a):
    rows.append(a)

def catalog(tag, to, kw1, kw2, kw3):
    rows = []
    t = tag
    for a, sa, b, sb in METS:
        add_row(
            rows,
            f"{sa}-{kw1}-{t}-stale", f"{t[0]}{sa}{kw1[:3]}-eval",
            f"{sb}-{kw1}-{t}-stale", f"{t[0]}{sb}{kw1[:3]}-eval",
            f"{a}({kw1}=['Actual Output'], threshold=0.{to})",
            f"{b}({kw1}=['Actual Output'], threshold=0.{to})",
            f"{a}({kw1}=['Actual Output'], threshold=0.{to + 10})",
            f"{b}({kw1}=['Actual Output'], threshold=0.{to + 10})",
            f"{a}({kw1}=EVAL_PARAMS, threshold=0.5)",
            f"{b}({kw1}=EVAL_PARAMS, threshold=0.5)",
            "metric",
        )
    return rows

def emit(mod, tag, to, kw1, kw2, kw3, offset, void_base, start_round, header):
    return len(catalog(tag, to, kw1, kw2, kw3))

def main():
    n_ac = emit(
        "mill_plants_ac", "bay", 21, "evaluation_params", "strictness", "max_tokens",
        876, 120, 1357, "header-ac",
    )
    emit(
        "mill_plants_ad", "rim", 23, "include_context", "debounce", "top_p",
        876 + n_ac, 132, 1357 + n_ac, "header-ad",
    )
"""


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", "origin/legacy-mill-lane:experiments/_gen_evh_plants_r801.py"],
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


class EvhSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FACTORY, "eval-harness-trajectory-factory")
        self.assertEqual(cv.GENERATOR, "grok-4.6")
        self.assertEqual(cv.PRESERVE_COMMIT, "66deb037890ec2b8177c3a07542bf623924037bb")
        self.assertEqual(cv.MILL_DIR, "scripts/eval_harness_unique_mill")

    def test_nine_sources_split_into_gens_and_loop(self):
        self.assertEqual(len(MILL_SOURCES), 9)
        self.assertEqual(len(catalog_sources()), 8)
        self.assertEqual(len(loop_sources()), 1)
        self.assertEqual(
            {source.companion_mill_path for source in MILL_SOURCES},
            {cv.MILL_DIR},
        )

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(
                path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path)
            )
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("evh-loop-r2761.py"))
        self.assertTrue(is_vendor_filename("_gen_evh_plants_r801.py"))
        self.assertTrue(is_vendor_filename("mill_plants_w.py"))
        self.assertTrue(is_vendor_filename("eval_harness_unique_mill.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/evh-loop-r2761.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "evh"
        hits = []
        for name in (
            "catalog_ast.py",
            "catalog_extract.py",
            "catalog.py",
            "identity.py",
            "leftover_plants.py",
            "leftover_plants_b.py",
            "pairs.py",
            "plants_extract.py",
        ):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_extractor_rebuilds_add_tables(self):
        extracted = extract_plant_catalog(
            _R801_SNIPPET, path="experiments/_gen_evh_plants_r801.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_ADD_TABLES)
        self.assertEqual(extracted["n_rows"], 1)
        dest = extracted["catalogs"][0]
        self.assertEqual(dest["dest"], "mill_plants_w")
        self.assertEqual(dest["first_slug"], "ansrel-strict-canary-stale")
        self.assertEqual(dest["pairs"][0]["fail_slug"], "halluc-strict-canary-stale")
        self.assertEqual(dest["pairs"][0]["success_plant"], "restock-void-59")
        self.assertEqual(dest["void_base"], 59)

    def test_extractor_reads_raw_literal(self):
        extracted = extract_plant_catalog(
            _RAW_SNIPPET, path="experiments/_gen_evh_plants_r927.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_RAW)
        self.assertEqual(extracted["n_rows"], 1)
        dest = extracted["catalogs"][0]
        self.assertEqual(dest["dest"], "mill_plants_x")
        self.assertEqual(dest["first_slug"], "ansrel-minscore-hold-stale")
        self.assertEqual(dest["pairs"][0]["fail_slug"], "halluc-minscore-hold-stale")
        self.assertEqual(dest["pairs"][0]["success_plant"], "restock-void-72")
        self.assertEqual(dest["offset"], 446)

    def test_extractor_reads_fstring_catalog(self):
        extracted = extract_plant_catalog(
            _FSTRING_SNIPPET, path="experiments/_gen_evh_plants_r1161.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_FSTRING)
        dest = extracted["catalogs"][0]
        self.assertEqual(dest["dest"], "mill_plants_aa")
        self.assertEqual(dest["first_slug"], "ansrel-embed-hub-stale")
        self.assertEqual(dest["pairs"][0]["fail_slug"], "halluc-embed-hub-stale")
        self.assertEqual(dest["void_base"], 96)
        self.assertEqual(dest["offset"], 680)

    def test_extractor_reads_param_emit_catalogs(self):
        extracted = extract_plant_catalog(
            _PARAM_SNIPPET, path="experiments/_gen_evh_plants_r1357.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_PARAM)
        self.assertEqual(extracted["n_catalogs"], 2)
        self.assertEqual(extracted["n_rows"], 2)
        first, second = extracted["catalogs"]
        self.assertEqual(first["dest"], "mill_plants_ac")
        self.assertEqual(first["tag"], "bay")
        self.assertEqual(first["first_slug"], "ansrel-evaluation_params-bay-stale")
        self.assertEqual(first["pairs"][0]["success_domain"], "bansreleva-eval")
        self.assertEqual(first["start_round"], 1357)
        self.assertEqual(second["dest"], "mill_plants_ad")
        self.assertEqual(second["tag"], "rim")
        self.assertEqual(second["offset"], 877)
        self.assertEqual(second["start_round"], 1358)
        self.assertEqual(second["void_base"], 132)

    def test_loop_mill_path_constant(self):
        source = (
            "ROOT = Path(__file__).resolve().parents[1]\n"
            'MILL = ROOT / "scripts" / "eval_harness_unique_mill"\n'
        )
        self.assertEqual(extract_companion_path(source), cv.MILL_DIR)

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 8)
        self.assertEqual(CATALOG.n_pair_rows, 1842)
        self.assertEqual(CATALOG.slice, "r801")
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        r801 = CATALOG.mills["_gen_evh_plants_r801"]
        self.assertEqual(r801.n_rows, 126)
        self.assertEqual(r801.catalog_first, 801)
        self.assertEqual(r801.first_slug, "ansrel-strict-canary-stale")
        self.assertEqual(r801.last_slug, "pytest-order-scope-module-canary-stale")
        self.assertEqual(len(r801.catalogs[0].pairs), 126)
        first_pair = r801.catalogs[0].pairs[0]
        self.assertEqual(first_pair["success_plant"], "restock-void-59")
        self.assertEqual(tuple(first_pair), PAIR_IDENTITY_KEYS)
        self.assertNotIn("first_ok", first_pair)
        self.assertEqual(CATALOG.mills["_gen_evh_plants_r927"].n_rows, 78)
        self.assertEqual(CATALOG.mills["_gen_evh_plants_r1161"].n_rows, 117)
        self.assertEqual(CATALOG.mills["_gen_evh_plants_r1357"].n_catalogs, 3)
        self.assertEqual(CATALOG.mills["_gen_evh_plants_r2761"].n_rows, 117)
        self.assertFalse(CATALOG.mills["_gen_evh_plants_r2761"].catalogs[0].pairs)
        self.assertEqual(CATALOG.n_deferred_pairs, cv.PAIRS_N_ROWS)
        self.assertEqual(cv.PAIRS_N_ROWS, 1716)


class EvhLegacyExtractTests(unittest.TestCase):
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
            live = extract_plant_catalog(text, path=source.path, blob_sha=source.blob_sha)
            committed = CATALOG.mills[source.mill_id]
            self.assertEqual(live["n_rows"], committed.n_rows, source.mill_id)
            self.assertEqual(live["first_slug"], committed.first_slug, source.mill_id)
            self.assertEqual(live["last_slug"], committed.last_slug, source.mill_id)
            self.assertEqual(live["catalog_first"], committed.catalog_first, source.mill_id)
            self.assertEqual(live["sha256"], committed.sha256, source.mill_id)
            self.assertEqual(live["shape"], committed.shape, source.mill_id)
            self.assertEqual(live["n_catalogs"], committed.n_catalogs, source.mill_id)
            mills.append(
                mill_summary(live, include_pairs=source.mill_id == cv.FIRST_SLICE_MILL_ID)
            )
        expected = json.loads(dumps_catalog(catalog_document(mills)))
        committed = json.loads(catalog_json_path().read_text(encoding="utf-8"))
        archive_b = committed.pop("archive_b")
        archive_c = committed.pop("archive_c")
        self.assertIsNotNone(archive_b)
        self.assertIsNotNone(archive_c)
        self.assertEqual(committed, expected)

    def test_loop_and_gen_scripts_name_companion_mill_dir(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        for source in MILL_SOURCES:
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
            self.assertEqual(list(dest.glob("evh-*.py")), [])
            self.assertEqual(list(dest.glob("_gen_evh_*.py")), [])
            self.assertEqual(list(dest.glob("mill_plants*.py")), [])

    def test_live_reextract_sample_matches_committed_rows(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        sample_id = "_gen_evh_plants_r927"
        source = source_by_id(sample_id)
        text = subprocess.check_output(
            ["git", "show", f"{cv.LEGACY_REF}:{source.path}"],
            text=True,
            cwd=REPO,
        )
        live = extract_plant_catalog(text, path=source.path, blob_sha=source.blob_sha)
        extracted = deferred_rows_from_extract(live)
        committed = [row for row in CATALOG.deferred_pairs if row["mill_id"] == sample_id]
        self.assertEqual(len(extracted), 78)
        self.assertEqual(extracted, committed)
        self.assertEqual(extracted[0]["success_slug"], "ansrel-minscore-hold-stale")
        self.assertEqual(extracted[-1]["success_slug"], "addopts-timeout-func-hold-stale")


class EvhArchiveBPlantsTests(unittest.TestCase):
    def test_leftover_plants_jsonl_stays_compact(self):
        path = leftover_plants_jsonl_path()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), cv.LEFTOVER_PLANTS_N_ROWS)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            row = json.loads(line)
            self.assertEqual(set(row), set(cv.LEFTOVER_PLANT_ROW_KEYS))

    def test_archive_b_rows_match_catalog_pins(self):
        archive = CATALOG.archive_b
        self.assertIsNotNone(archive)
        assert archive is not None
        self.assertEqual(archive.path, cv.ARCHIVE_B_PATH)
        self.assertEqual(archive.n_pairs, cv.LEFTOVER_PLANTS_N_ROWS)
        self.assertEqual(len(archive.pairs), cv.LEFTOVER_PLANTS_N_ROWS)
        self.assertEqual(archive.pairs[0]["ok_slug"], "gha-restore-keys-cache-x63e")
        self.assertEqual(archive.pairs[-1]["ok_slug"], "otel-baggage-score-overwrite-d69k")

    def test_live_reextract_archive_b_matches_committed(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        text = subprocess.check_output(
            [
                "git",
                "show",
                f"{cv.ARCHIVE_B_LEGACY_COMMIT}:{cv.ARCHIVE_B_PATH}",
            ],
            text=True,
            cwd=REPO,
        )
        extracted = extract_leftover_plant_pairs(text)
        committed = list(load_leftover_plants())
        self.assertEqual(len(extracted), cv.LEFTOVER_PLANTS_N_ROWS)
        self.assertEqual(extracted, committed)


class EvhArchiveCPlantsTests(unittest.TestCase):
    def test_leftover_plants_b_jsonl_stays_compact(self):
        path = leftover_plants_b_jsonl_path()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), cv.LEFTOVER_PLANTS_B_N_ROWS)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            row = json.loads(line)
            self.assertEqual(set(row), set(cv.LEFTOVER_PLANT_ROW_KEYS))
            self.assertEqual(row["source"], cv.ARCHIVE_C_PATH)

    def test_archive_c_rows_match_catalog_pins(self):
        archive = CATALOG.archive_c
        self.assertIsNotNone(archive)
        assert archive is not None
        self.assertEqual(archive.path, cv.ARCHIVE_C_PATH)
        self.assertEqual(archive.n_pairs, cv.LEFTOVER_PLANTS_B_N_ROWS)
        self.assertEqual(len(archive.pairs), cv.LEFTOVER_PLANTS_B_N_ROWS)
        self.assertEqual(archive.pairs[0]["ok_slug"], "prettier-json-sort-bind-f71m")
        self.assertEqual(archive.pairs[-1]["ok_slug"], "instructor-ge-retry-swallow-l77s")

    def test_live_reextract_archive_c_matches_committed(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        text = subprocess.check_output(
            [
                "git",
                "show",
                f"{cv.ARCHIVE_C_LEGACY_COMMIT}:{cv.ARCHIVE_C_PATH}",
            ],
            text=True,
            cwd=REPO,
        )
        extracted = extract_leftover_plant_pairs(text, path=cv.ARCHIVE_C_PATH)
        committed = list(load_leftover_plants_b())
        self.assertEqual(len(extracted), cv.LEFTOVER_PLANTS_B_N_ROWS)
        self.assertEqual(extracted, committed)


class EvhDeferredPairsTests(unittest.TestCase):
    def test_pairs_jsonl_stays_compact(self):
        path = pairs_jsonl_path()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), cv.PAIRS_N_ROWS)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        self.assertEqual(len(lines), 1716)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            row = json.loads(line)
            self.assertEqual(tuple(row), PAIR_ROW_KEYS)
            self.assertNotIn("pairs", row)
            self.assertNotIn("catalogs", row)

    def test_deferred_rows_match_catalog_dest_counts(self):
        pairs = CATALOG.deferred_pairs
        self.assertEqual(len(pairs), 1716)
        deferred_ids = {
            source.mill_id
            for source in catalog_sources()
            if source.mill_id != cv.FIRST_SLICE_MILL_ID
        }
        self.assertEqual({row["mill_id"] for row in pairs}, deferred_ids)
        expected = {
            "_gen_evh_plants_r927": 78,
            "_gen_evh_plants_r1161": 117,
            "_gen_evh_plants_r1357": 351,
            "_gen_evh_plants_r1708": 351,
            "_gen_evh_plants_r2059": 351,
            "_gen_evh_plants_r2410": 351,
            "_gen_evh_plants_r2761": 117,
        }
        counts: dict[str, int] = {mill_id: 0 for mill_id in expected}
        for row in pairs:
            counts[row["mill_id"]] += 1
        self.assertEqual(counts, expected)
        self.assertEqual(pairs[0]["dest"], "mill_plants_x")
        self.assertEqual(pairs[-1]["dest"], "mill_plants_ao")
        self.assertEqual(set(pairs[0]), set(PAIR_ROW_KEYS))

    def test_loader_fails_closed_on_a_missing_pair_field(self):
        lines = pairs_jsonl_path().read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        del first["fail_slug"]
        lines[0] = json.dumps(first, separators=(",", ":"))
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "pairs.jsonl"
            dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "keys differ"):
                load_pairs(dest)

    def test_loader_fails_closed_on_nested_dest_objects(self):
        nested = json.dumps(
            {"dest": "mill_plants_x", "mill_id": "_gen_evh_plants_r927", "pairs": []},
            separators=(",", ":"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "pairs.jsonl"
            dest.write_text(nested + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nests dest objects"):
                load_pairs(dest)


if __name__ == "__main__":
    unittest.main()
