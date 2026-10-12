#!/usr/bin/env python3
"""lef catalog extract: full r629+r728+r968 slice, no vendored mills."""

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

from lef.catalog import CATALOG  # noqa: E402
from lef.plants_extract import (  # noqa: E402
    dumps_plants_jsonl,
    extract_mill_plants_record,
    extract_plant_pairs,
    plants_jsonl_path,
    sha256_bytes as plants_sha256_bytes,
)
from lef.catalog_extract import (  # noqa: E402
    SHAPE_STEMS,
    SHAPE_TABLES,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    dumps_rows,
    extract_companion_path,
    extract_mill_catalog,
    extract_nums_formula,
    extract_slugs_listing,
    mill_summary,
    nums_at,
)
from lef.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from lef.sources import (  # noqa: E402
    MILL_SOURCES,
    PLANT_B_SOURCE,
    PLANT_SOURCE,
    catalog_sources,
    loop_sources,
    plant_sources,
    slug_sources,
)
from lef import vocabulary as lv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_TABLES_SNIPPET = """
FACTORY = "llm-eval-flakiness-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 629
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
CACHE_OK = [
    ("azure-api-version-unkeyed", "azure_api_version", 0.93, 0.21, 0.9,
     "2024-02-01", "2024-06-01", "avoided-a", "ticket-a"),
]
LAST_BAD = [
    ("toolcall-last-only", "last tool call", 0.88, 0.11, 0.79,
     "refund.confirm", "refund.lookup", "avoided-b", "ticket-b"),
]
SEED_OK = [
    ("fewshot-includes-item", "few-shot pool", "cl12-40d", 0.97, 0.18, 0.81,
     "avoided-c", "ticket-c"),
]
TEMP0_BAD = [
    ("hf-dosample-temp0", "HF generate", "avoided-d", "ticket-d", 0.19, 0.84, 0.7),
]
ALIAS_OK = [
    ("helpful-vs-helpfulness", "helpfulness", "helpful_v1", "helpfulness_v3",
     0.91, 0.22, 0.8, "avoided-e", "ticket-e"),
]
TRUNC_BAD = [
    ("tool-json-4k-cut", "4096", "8192", "avoided-f", "ticket-f", 0.91, 0.16, 0.8),
]
CACHE_OK += [
    ("html-sanitizer-unkeyed", "sanitizer", 0.87, 0.24, 0.66,
     "bleach", "nh3", "avoided-g", "ticket-g"),
]
LAST_BAD += [
    ("sql-last-cte", "last SQL CTE", 0.89, 0.17, 0.73,
     "final_select", "pii_join", "avoided-h", "ticket-h"),
]
SEED_OK += [
    ("dev-split-alias-eval", "config split", "dev->eval", 0.91, 0.19, 0.77,
     "avoided-i", "ticket-i"),
]
TEMP0_BAD += [
    ("toolchoice-auto-temp0", "tool_choice=auto", "avoided-j", "ticket-j",
     0.18, 0.82, 0.67),
]
ALIAS_OK += [
    ("winrate-as-bt", "winrate", "mean_winrate", "bt_score",
     0.86, 0.22, 0.7, "avoided-k", "ticket-k"),
]
_TRUNC_MORE = [
    ("iso-first-extent", "first ISO extent", "full image", "avoided-l",
     "ticket-l", 0.87, 0.16, 0.73),
]
TRUNC_BAD += _TRUNC_MORE
"""

_STEMS_SNIPPET = """
FACTORY = "llm-eval-flakiness-factory"
CATALOG_FIRST = 968
BANNED_SLUGS = frozenset({"conll-coref-avg", "nbd-live-as-gpt"})
STEMS = [
    ("tsc-offset", "0", "200"),
    ("iwd-roam", "on", "off"),
]
FROMS = ["score", "gptscore"]
CANONS = ["policy_score", "gptscore"]
LIMS = [("16", "80"), ("8192", "65536")]

def _nums(i: int) -> tuple[float, float, float]:
    hi = round(0.86 + (i % 8) * 0.01, 2)
    lo = round(0.14 + (i % 9) * 0.01, 2)
    mid = round(0.70 + (i % 7) * 0.01, 2)
    return hi, lo, mid

def build_catalogs():
    return [], [], [], [], [], []

CACHE_OK, LAST_BAD, SEED_OK, TEMP0_BAD, ALIAS_OK, TRUNC_BAD = build_catalogs()
"""


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", "origin/legacy-mill-lane:experiments/lef-mill-r629.py"],
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


class LefSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[lv.FAMILY_PREFIX], lv.FACTORY)
        self.assertEqual(lv.FACTORY, "llm-eval-flakiness-factory")
        self.assertEqual(lv.GENERATOR, "grok-4.6")
        self.assertEqual(lv.PRESERVE_COMMIT, "02d05373e4144ab609ec141b28fd4c52a4174f21")

    def test_seven_sources_split_into_mills_loops_and_slugs(self):
        self.assertEqual(len(MILL_SOURCES), 7)
        self.assertEqual(len(catalog_sources()), 3)
        self.assertEqual(len(loop_sources()), 3)
        self.assertEqual(len(slug_sources()), 1)
        self.assertEqual(
            {source.companion_mill_path for source in loop_sources()},
            {
                "experiments/lef-mill-r629.py",
                "experiments/lef-mill-r728.py",
                "experiments/lef-mill-r968.py",
            },
        )

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in lv.FORBIDDEN_MILL_GLOBS:
            hits.extend(
                path
                for path in REPO.rglob(pattern)
                if "legacy-mill-lane" not in str(path)
            )
        self.assertEqual(hits, [])
        self.assertEqual(list((REPO / "pipelines" / "lef").glob(lv.SLUGS_FILENAME)), [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("lef-mill-r629.py"))
        self.assertTrue(is_vendor_filename("lef-loop-r629.py"))
        self.assertTrue(is_vendor_filename(".lef-used-slugs.txt"))
        self.assertTrue(is_vendor_filename("mill_plants.py"))
        self.assertTrue(is_vendor_filename("mill_plants_b.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        self.assertFalse(is_vendor_filename("plants.jsonl"))
        self.assertFalse(is_vendor_filename("leftover_mill.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/lef-mill-r629.py")])
        with self.assertRaises(SystemExit):
            refuse_vendor_paths(
                [Path("scripts/llm_eval_flakiness_mill/mill_plants.py")]
            )

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "lef"
        hits = []
        for name in (
            "catalog_ast.py",
            "catalog_extract.py",
            "catalog.py",
            "identity.py",
            "plants_extract.py",
        ):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_archive_b_plant_source_pins(self):
        self.assertEqual(len(plant_sources()), 2)
        self.assertEqual(PLANT_SOURCE.mill_id, lv.PLANTS_MILL_ID)
        self.assertEqual(PLANT_SOURCE.path, lv.PLANTS_SOURCE_PATH)
        self.assertEqual(PLANT_SOURCE.blob_sha, lv.PLANTS_BLOB_SHA)
        self.assertEqual(PLANT_B_SOURCE.mill_id, lv.PLANTS_B_MILL_ID)
        self.assertEqual(PLANT_B_SOURCE.path, lv.PLANTS_B_SOURCE_PATH)
        self.assertEqual(PLANT_B_SOURCE.blob_sha, lv.PLANTS_B_BLOB_SHA)

    def test_committed_plants_catalog(self):
        self.assertIsNotNone(CATALOG.plants)
        plants = CATALOG.plants
        assert plants is not None
        self.assertEqual(plants.n_pairs, lv.PLANTS_PAIR_COUNT)
        self.assertEqual(plants.catalog_first, lv.PLANTS_CATALOG_FIRST)
        self.assertEqual(plants.first_ok_slug, "kappa-vs-geval-align")
        self.assertEqual(plants.last_ok_slug, "diff-sorted-truncate")
        self.assertEqual(plants.archive_commit, lv.ARCHIVE_B_COMMIT)
        self.assertEqual(len(plants.pairs), lv.PLANTS_PAIR_COUNT)
        self.assertTrue(plants.pairs[0].ok["success"])
        self.assertFalse(plants.pairs[0].bad["success"])

    def test_committed_plants_b_catalog(self):
        self.assertIsNotNone(CATALOG.plants_b)
        plants_b = CATALOG.plants_b
        assert plants_b is not None
        self.assertEqual(plants_b.n_pairs, lv.PLANTS_B_PAIR_COUNT)
        self.assertEqual(plants_b.catalog_first, lv.PLANTS_B_CATALOG_FIRST)
        self.assertEqual(plants_b.first_ok_slug, "annotator-id-unkeyed")
        self.assertEqual(plants_b.last_ok_slug, "fleiss-vs-two-rater")
        self.assertEqual(plants_b.archive_commit, lv.ARCHIVE_B_COMMIT)
        self.assertEqual(plants_b.plants_file, lv.PLANTS_B_FILENAME)
        self.assertEqual(len(plants_b.pairs), lv.PLANTS_B_PAIR_COUNT)
        self.assertTrue(plants_b.pairs[0].ok["success"])
        self.assertFalse(plants_b.pairs[0].bad["success"])

    def test_plants_jsonl_is_compact(self):
        path = plants_jsonl_path()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), lv.PLANTS_PAIR_COUNT)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            json.loads(line)

    def test_plants_b_jsonl_is_compact(self):
        path = plants_jsonl_path(filename=lv.PLANTS_B_FILENAME)
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), lv.PLANTS_B_PAIR_COUNT)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            json.loads(line)

    def test_dumps_plants_rebuilds_committed_jsonl(self):
        path = plants_jsonl_path()
        rebuilt = dumps_plants_jsonl(
            [{"ok": pair.ok, "bad": pair.bad} for pair in CATALOG.plants.pairs],  # type: ignore[union-attr]
            mill_id=lv.PLANTS_MILL_ID,
            source=lv.PLANTS_SOURCE_PATH,
            base_round=lv.PLANTS_CATALOG_FIRST,
        )
        self.assertEqual(rebuilt, path.read_text(encoding="utf-8"))

    def test_dumps_plants_b_rebuilds_committed_jsonl(self):
        path = plants_jsonl_path(filename=lv.PLANTS_B_FILENAME)
        rebuilt = dumps_plants_jsonl(
            [{"ok": pair.ok, "bad": pair.bad} for pair in CATALOG.plants_b.pairs],  # type: ignore[union-attr]
            mill_id=lv.PLANTS_B_MILL_ID,
            source=lv.PLANTS_B_SOURCE_PATH,
            base_round=lv.PLANTS_B_CATALOG_FIRST,
        )
        self.assertEqual(rebuilt, path.read_text(encoding="utf-8"))

    def test_extractor_reads_tables_and_augassign(self):
        extracted = extract_mill_catalog(
            _TABLES_SNIPPET, path="experiments/lef-mill-r629.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_TABLES)
        self.assertEqual(extracted["catalog_first"], 629)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "azure-api-version-unkeyed")
        self.assertEqual(extracted["last_slug"], "html-sanitizer-unkeyed")
        self.assertEqual(extracted["tables"]["TRUNC_BAD"][1][0], "iso-first-extent")
        self.assertEqual(extracted["banned_keys"], list(lv.BANNED_KEYS))

    def test_extractor_rebuilds_stems_without_exec(self):
        extracted = extract_mill_catalog(
            _STEMS_SNIPPET, path="experiments/lef-mill-r968.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_STEMS)
        self.assertEqual(extracted["catalog_first"], 968)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "tsc-offset-unkeyed")
        self.assertEqual(extracted["last_slug"], "iwd-roam-unkeyed")
        self.assertEqual(extracted["banned_slugs"], ["conll-coref-avg", "nbd-live-as-gpt"])
        self.assertEqual(extracted["nums"], lv.NUMS_FORMULA)
        hi, lo, mid = nums_at(0, lv.NUMS_FORMULA)
        self.assertEqual(extracted["tables"]["CACHE_OK"][0][2:5], (hi, lo, mid))

    def test_nums_formula_from_function_ast(self):
        tree = ast.parse(_STEMS_SNIPPET)
        self.assertEqual(extract_nums_formula(tree), lv.NUMS_FORMULA)

    def test_loop_mill_path_constant(self):
        source = (
            "ROOT = Path(__file__).resolve().parents[1]\n"
            'LEF_MILL = ROOT / "experiments" / "lef-mill-r629.py"\n'
        )
        self.assertEqual(
            extract_companion_path(source),
            "experiments/lef-mill-r629.py",
        )

    def test_committed_catalog_counts(self):
        self.assertIsNotNone(CATALOG)
        self.assertEqual(len(CATALOG.mills), 3)
        self.assertEqual(CATALOG.n_catalog_rows, 682)
        self.assertEqual(CATALOG.n_pair_slots, 2046)
        self.assertEqual(CATALOG.n_table_rows, 4092)
        self.assertEqual(CATALOG.slice, "full")
        self.assertEqual(CATALOG.preserve_commit, lv.PRESERVE_COMMIT)
        self.assertEqual(tuple(CATALOG.mills), lv.COMMITTED_MILL_IDS)
        r629 = CATALOG.mills["lef-mill-r629"]
        self.assertEqual(r629.n_rows, 48)
        self.assertEqual(r629.catalog_first, 629)
        self.assertEqual(r629.first_slug, "azure-api-version-unkeyed")
        self.assertEqual(r629.last_slug, "candidate-count-unkeyed")
        self.assertEqual(len(r629.tables["CACHE_OK"]), 48)
        r728 = CATALOG.mills["lef-mill-r728"]
        self.assertEqual(r728.n_rows, 80)
        self.assertEqual(r728.first_slug, "cuda-graph-capture-unkeyed")
        self.assertEqual(r728.last_slug, "nbd-timeout-unkeyed")
        self.assertEqual(r728.banned_slugs, ("conll-coref-avg", "simpson-policy-mix"))
        self.assertEqual(len(r728.tables["CACHE_OK"]), 80)
        self.assertEqual(r728.tables["CACHE_OK"][0][0], r728.first_slug)
        self.assertEqual(r728.tables["CACHE_OK"][-1][0], r728.last_slug)
        r968 = CATALOG.mills["lef-mill-r968"]
        self.assertEqual(r968.n_rows, 554)
        self.assertEqual(r968.shape, SHAPE_STEMS)
        self.assertEqual(r968.first_slug, "tsc-offset-unkeyed")
        self.assertEqual(r968.last_slug, "iwd-roam-unkeyed")
        self.assertEqual(len(r968.tables["CACHE_OK"]), 554)
        self.assertEqual(r968.tables["CACHE_OK"][0][0], r968.first_slug)
        self.assertEqual(r968.tables["CACHE_OK"][-1][0], r968.last_slug)
        self.assertIsNone(r968.stems)
        self.assertEqual(r968.nums, lv.NUMS_FORMULA)
        self.assertEqual(CATALOG.slugs.n_rows, 2095)
        self.assertEqual(CATALOG.slugs.first_slug, "3pl-guess-c-vs-pct")
        self.assertEqual(CATALOG.slugs.last_slug, "zstd-window-cut")

    def test_committed_header_omits_deferred_payloads(self):
        header = json.loads(
            (REPO / "pipelines" / "lef" / "CATALOG.json").read_text(encoding="utf-8")
        )
        self.assertEqual(header["slice_rows_file"], lv.ROWS_FILENAME)
        self.assertEqual(header["slice_mill"], lv.SLICE_MILL_ID)
        for mill_id, row in header["mills"].items():
            self.assertNotIn("tables", row, mill_id)
            self.assertNotIn("stems", row, mill_id)
            self.assertNotIn("froms", row, mill_id)
            self.assertNotIn("canons", row, mill_id)
            self.assertNotIn("lims", row, mill_id)

    def test_slice_rows_jsonl_is_compact(self):
        path = REPO / "pipelines" / "lef" / lv.ROWS_FILENAME
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), lv.COMMITTED_ROW_COUNT)
        self.assertEqual(len(lines), 48 + 80 + 554)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        parsed = []
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            parsed.append(json.loads(line))
        self.assertEqual(parsed[0]["i"], 0)
        self.assertEqual(parsed[-1]["i"], lv.COMMITTED_ROW_COUNT - 1)
        self.assertEqual(parsed[0]["CACHE_OK"][0], "azure-api-version-unkeyed")
        self.assertEqual(parsed[47]["CACHE_OK"][0], "candidate-count-unkeyed")
        self.assertEqual(parsed[48]["CACHE_OK"][0], "cuda-graph-capture-unkeyed")
        self.assertEqual(parsed[127]["CACHE_OK"][0], "nbd-timeout-unkeyed")
        self.assertEqual(parsed[128]["CACHE_OK"][0], "tsc-offset-unkeyed")
        self.assertEqual(parsed[681]["CACHE_OK"][0], "iwd-roam-unkeyed")

    def test_dumps_rows_rebuilds_committed_jsonl(self):
        path = REPO / "pipelines" / "lef" / lv.ROWS_FILENAME
        start = 0
        chunks = []
        for mill_id in lv.COMMITTED_MILL_IDS:
            mill = CATALOG.mills[mill_id]
            chunks.append(dumps_rows(mill.tables, start_index=start))
            start += mill.n_rows
        self.assertEqual("".join(chunks), path.read_text(encoding="utf-8"))
        self.assertEqual(start, lv.COMMITTED_ROW_COUNT)


class LefLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        mills = []
        for source in catalog_sources():
            text = subprocess.check_output(
                ["git", "show", f"{lv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            blob = subprocess.check_output(
                ["git", "rev-parse", f"{lv.LEGACY_REF}:{source.path}"],
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
            for name in lv.TABLE_NAMES:
                self.assertEqual(
                    tuple(tuple(row) for row in live["tables"][name]),
                    committed.tables[name],
                    source.mill_id,
                )
            mills.append(mill_summary(live, include_tables=False))
        slugs_source = slug_sources()[0]
        slugs_text = subprocess.check_output(
            ["git", "show", f"{lv.LEGACY_REF}:{slugs_source.path}"],
            text=True,
            cwd=REPO,
        )
        slugs = extract_slugs_listing(
            slugs_text,
            path=slugs_source.path,
            blob_sha=slugs_source.blob_sha,
        )
        self.assertEqual(slugs["n_rows"], CATALOG.slugs.n_rows)
        self.assertEqual(slugs["sha256"], CATALOG.slugs.sha256)
        committed_header = json.loads(
            catalog_json_path().read_text(encoding="utf-8")
        )
        committed_header.pop("plants", None)
        committed_header.pop("plants_b", None)
        self.assertEqual(
            dumps_catalog(catalog_document(mills, slugs=slugs)),
            json.dumps(committed_header, ensure_ascii=True, indent=2, sort_keys=True)
            + "\n",
        )

    def test_loop_scripts_name_companion_mills(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        for source in loop_sources():
            text = subprocess.check_output(
                ["git", "show", f"{lv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            self.assertEqual(
                extract_companion_path(text),
                source.companion_mill_path,
                source.mill_id,
            )

    def test_r728_source_mentions_exec_module_but_extract_does_not_run_it(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        text = subprocess.check_output(
            ["git", "show", f"{lv.LEGACY_REF}:experiments/lef-mill-r728.py"],
            text=True,
            cwd=REPO,
        )
        self.assertIn("exec_module", text)
        live = extract_mill_catalog(
            text,
            path="experiments/lef-mill-r728.py",
            blob_sha="b8afb84386270b05c39d756fb6ac1ca48107faf1",
        )
        self.assertEqual(live["n_rows"], 80)
        self.assertNotIn("lef_mill_r629", live)

    def test_git_show_is_the_only_legacy_read(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            refuse_vendor_paths(dest.rglob("*") if dest.exists() else ())
            self.assertEqual(list(dest.glob("lef-mill*.py")), [])

    def test_archive_b_plants_match_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        text = subprocess.check_output(
            ["git", "show", f"{lv.ARCHIVE_B_COMMIT}:{lv.PLANTS_SOURCE_PATH}"],
            text=True,
            cwd=REPO,
        )
        blob = subprocess.check_output(
            ["git", "rev-parse", f"{lv.ARCHIVE_B_COMMIT}:{lv.PLANTS_SOURCE_PATH}"],
            text=True,
            cwd=REPO,
        ).strip()
        self.assertEqual(blob, PLANT_SOURCE.blob_sha)
        live_pairs = extract_plant_pairs(text, path=lv.PLANTS_SOURCE_PATH)
        self.assertEqual(len(live_pairs), lv.PLANTS_PAIR_COUNT)
        record = extract_mill_plants_record(
            text,
            path=lv.PLANTS_SOURCE_PATH,
            blob_sha=blob,
            archive_commit=lv.ARCHIVE_B_COMMIT,
            mill_id=lv.PLANTS_MILL_ID,
            catalog_first=lv.PLANTS_CATALOG_FIRST,
        )
        committed = CATALOG.plants
        assert committed is not None
        self.assertEqual(record["n_pairs"], committed.n_pairs)
        self.assertEqual(record["first_ok_slug"], committed.first_ok_slug)
        self.assertEqual(record["last_ok_slug"], committed.last_ok_slug)
        self.assertEqual(record["sha256"], committed.sha256)
        live_jsonl = dumps_plants_jsonl(
            live_pairs,
            mill_id=lv.PLANTS_MILL_ID,
            source=lv.PLANTS_SOURCE_PATH,
            base_round=lv.PLANTS_CATALOG_FIRST,
        )
        self.assertEqual(
            plants_sha256_bytes(live_jsonl.encode()),
            committed.plants_sha256,
        )
        self.assertEqual(
            live_jsonl,
            plants_jsonl_path().read_text(encoding="utf-8"),
        )

    def test_archive_b_plants_b_match_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        text = subprocess.check_output(
            ["git", "show", f"{lv.ARCHIVE_B_COMMIT}:{lv.PLANTS_B_SOURCE_PATH}"],
            text=True,
            cwd=REPO,
        )
        blob = subprocess.check_output(
            ["git", "rev-parse", f"{lv.ARCHIVE_B_COMMIT}:{lv.PLANTS_B_SOURCE_PATH}"],
            text=True,
            cwd=REPO,
        ).strip()
        self.assertEqual(blob, PLANT_B_SOURCE.blob_sha)
        live_pairs = extract_plant_pairs(
            text,
            path=lv.PLANTS_B_SOURCE_PATH,
            append_list=lv.PLANTS_APPEND_LIST_B,
        )
        self.assertEqual(len(live_pairs), lv.PLANTS_B_PAIR_COUNT)
        record = extract_mill_plants_record(
            text,
            path=lv.PLANTS_B_SOURCE_PATH,
            blob_sha=blob,
            archive_commit=lv.ARCHIVE_B_COMMIT,
            mill_id=lv.PLANTS_B_MILL_ID,
            catalog_first=lv.PLANTS_B_CATALOG_FIRST,
            append_list=lv.PLANTS_APPEND_LIST_B,
            expected_pairs=lv.PLANTS_B_PAIR_COUNT,
            plants_file=lv.PLANTS_B_FILENAME,
        )
        committed = CATALOG.plants_b
        assert committed is not None
        self.assertEqual(record["n_pairs"], committed.n_pairs)
        self.assertEqual(record["first_ok_slug"], committed.first_ok_slug)
        self.assertEqual(record["last_ok_slug"], committed.last_ok_slug)
        self.assertEqual(record["sha256"], committed.sha256)
        live_jsonl = dumps_plants_jsonl(
            live_pairs,
            mill_id=lv.PLANTS_B_MILL_ID,
            source=lv.PLANTS_B_SOURCE_PATH,
            base_round=lv.PLANTS_B_CATALOG_FIRST,
        )
        self.assertEqual(
            plants_sha256_bytes(live_jsonl.encode()),
            committed.plants_sha256,
        )
        self.assertEqual(
            live_jsonl,
            plants_jsonl_path(filename=lv.PLANTS_B_FILENAME).read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
