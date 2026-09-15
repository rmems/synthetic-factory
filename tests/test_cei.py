#!/usr/bin/env python3
"""CEI mill package: catalog pins, AST extract, generate, CLI, no leftover mills."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURE = REPO / "tests" / "fixtures" / "cei"
COMMITTED = REPO / "config" / "cei"

sys.path.insert(0, str(PIPELINES))

from cei import catalog, cli, generate  # noqa: E402
from cei._contract import (  # noqa: E402
    FACTORY,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_LEFTOVER3_EXEC,
    FINDING_LOOP_REFUSED,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_USAGE,
    GENERATOR,
    LEFTOVER3_MILL_ID,
    LEFTOVER3_PATH,
    LEFTOVER3_ROUND,
    LEFTOVER3_SHAPE,
    MILL_PREFIX,
    SHAPE_OK_BAD,
    SOURCE_COMMIT,
    SOURCE_MILL_ID,
    SLICE3_R137_MILL_ID,
    SLICE3_R137_PATH,
    SLICE3_R137_ROUND,
    SLICE3_R42_MILL_ID,
    SLICE3_R42_PATH,
    SLICE3_R42_ROUND,
    SLICE3_R65_MILL_ID,
    SLICE3_R65_PATH,
    SLICE3_R65_ROUND,
    SOURCE_PATH,
    SOURCE_ROUND,
    CeiRefusal,
)
from mill_family import REVIEWED_MILL_PREFIX_HOMES, mill_prefix  # noqa: E402
from record_kind import classify_kind  # noqa: E402

EXPECTED_OK_SLUGS = (
    "csv-sniffer-vs-header",
    "xlsx-date1904-vs-serial",
    "parquet-bloom-vs-stats",
    "geojson-crs84-vs-bbox",
    "shapefile-shx-vs-dbf",
    "las-vlr-vs-point",
    "netcdf-cf-vs-coord",
    "fits-header-vs-table",
    "sqlite-schema-vs-pages",
    "csv-escape-vs-quote",
    "xlsx-defined-name-vs-used",
    "arrow-schema-vs-body",
    "csv-byte-order-vs-utf8",
    "xlsx-pivotcache-vs-sheet",
    "jsonl-schema-vs-row",
    "xlsx-theme-vs-cellfill",
    "csv-rfc4180-vs-split",
    "parquet-dict-vs-plain",
    "xlsx-table-vs-list",
    "csv-skipinitial-vs-pad",
    "csv-lineterm-vs-row",
    "xlsx-comments-vs-cell",
    "parquet-pageidx-vs-rowgroup",
    "wkt-vs-wkb",
    "csv-strict-vs-rest",
    "xlsx-autofilter-vs-used",
    "csv-unix-vs-excel",
    "parquet-int96-vs-ts",
    "xlsx-hyperlink-vs-text",
    "csv-doublequote-vs-escape",
    "xlsx-phonetic-vs-run",
    "csv-fieldsize-vs-chunk",
    "xlsx-datavalid-vs-cell",
    "csv-restval-vs-pad",
    "xlsx-sparkline-vs-chart",
    "csv-dialect-register-vs-excel",
    "xlsx-customxml-vs-sheet",
    "csv-quoting-none-vs-min",
    "xlsx-vml-vs-comment",
)
EXPECTED_R42_OK_SLUGS = (
    "parquet-footer-vs-drop",
    "avro-sync-vs-drop",
    "hdf5-attr-vs-drop",
    "stata-dta-cache-vs-drop",
    "numbers-iwa-vs-drop",
    "csv-dialect-cache-vs-drop",
    "arrow-ipc-vs-drop",
)
EXPECTED_R65_OK_SLUGS = (
    "xlsb-pivotcache-vs-drop",
    "mdb-system-vs-drop",
    "jsonl-jsonschema-vs-drop",
    "xmlss-styles-vs-drop",
    "lotus-wk1-fmt-vs-drop",
    "fst-hash-vs-drop",
    "lance-manifest-vs-drop",
    "xlsx-sharedstrings-vs-drop",
    "csv-crlf-vs-drop",
    "feather-footer-vs-drop",
    "iceberg-manifest-list-vs-drop",
    "csv-comment-header-vs-drop",
)
EXPECTED_R137_OK_SLUGS = (
    "matlab-mat-vs-drop",
    "lance-frag-vs-drop",
    "grib2-idx-vs-drop",
    "gpkg-rtree-vs-drop",
    "topojson-arcs-vs-drop",
    "kmz-overlay-vs-drop",
    "geotiff-overviews-vs-drop",
    "xltm-macrosheet-vs-drop",
    "sylk-format-vs-drop",
    "wq1-cell-vs-drop",
    "psv-header-vs-drop",
    "ini-section-vs-drop",
    "msgpack-ext-vs-drop",
    "bson-oid-vs-drop",
    "capnp-schema-vs-drop",
)
EXPECTED_R48_OK_SLUGS = (
    "parquet-columnindex-vs-drop",
    "avro-schema-vs-drop",
    "hdf5-btree-vs-drop",
    "stata-strl-vs-drop",
    "numbers-preview-vs-drop",
    "fods-styles-vs-drop",
    "arrow-dict-vs-drop",
    "csv-sniffer-vs-drop",
    "parquet-pageindex-vs-drop",
    "avro-codec-vs-drop",
    "hdf5-ohdr-vs-drop",
    "stata-frame-vs-drop",
    "numbers-thumb-vs-drop",
    "fods-meta-vs-drop",
    "arrow-tensor-vs-drop",
    "csv-utf16le-vs-drop",
)
TINY_LEFTOVER3_SOURCE = """
PAIRS = [
    (
        S(
            "tiny-parquet-vs-drop",
            "tinypq",
            "invoices.parquet",
            "tiny leftover sidecar",
            "unlink invoices.parquet",
            "os.unlink(path)",
            "bind leftover then drop",
            "test_tiny_not_drop",
            "https://example.test/a",
            "https://example.test/b",
            "tiny leftover survives unlink.",
            "Bind leftover. Not clone.",
            "AssertionError: unlinked; leftover remains",
            "AssertionError: unlink leaves leftover",
            "Naive unlink, then bind leftover.",
            "Bind leftover sidecar; do not treat unlink as drop.",
            "tiny-sidecar-vs-unlink",
            "tiny leftover stack",
            "sidecar bound then dropped (success).",
            "Plan change: Bind leftover. Unlink is not drop.",
        ),
        S(
            "tiny-orc-vs-drop",
            "tinyor",
            "invoices.orc",
            "tiny leftover cache",
            "unlink invoices.orc",
            "path.unlink()",
            "platform leftover reader",
            "test_tiny_orc_not_drop",
            "https://example.test/c",
            "https://example.test/d",
            "tiny leftover survives unlink.",
            "Need leftover binder. Handoff TINY-ORC-16.",
            "AssertionError: unlinked; leftover remains",
            "AssertionError: unlink cannot drop leftover",
            "Naive unlink, then hand off leftover.",
            "Do not treat unlink as drop while leftover remains.",
            "tiny-leftover-vs-unlink",
            "tiny leftover cache",
            "Still leftover after unlink; handoff TINY-ORC-16.",
            "Plan change: leftover is platform. Handoff TINY-ORC-16.",
            "TINY-ORC-16",
        ),
    )
]
"""

TINY_SOURCE = """
CATALOG_FIRST = 7
PAIRS = [
    (
        _ok(
            "tiny-csv-sniffer",
            "Honor csv.Sniffer dialect.",
            "csvsni",
            "csv.Sniffer dialect",
            "https://docs.python.org/3/library/csv.html",
            "return {'header': True}",
            "    return {'header': False}",
            "    return {'kind': 'csvsni', 'dialect': 'sniffed'}",
        ),
        _bad(
            "tiny-dbase-handoff",
            "Hand off dBase memo.",
            "dbfmem",
            "dBase memo .dbt",
            "https://example.test/dbt",
            "return {'rows': True}",
            "    return {'rows': False}",
            "DBF-TINY-7",
        ),
    )
]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogLoading(unittest.TestCase):
    def test_committed_catalog_loads_r81_r48_and_slice3_ast_extracted_pairs(self):
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(loaded.catalog_id, "cei-pairs-v1")
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(FACTORY, REVIEWED_MILL_PREFIX_HOMES[MILL_PREFIX])
        self.assertEqual(len(loaded.plants), 89)
        self.assertEqual(len(loaded.mills), 5)
        r81 = [plant for plant in loaded.plants if plant.mill_id == SOURCE_MILL_ID]
        r48 = [plant for plant in loaded.plants if plant.mill_id == LEFTOVER3_MILL_ID]
        r42 = [plant for plant in loaded.plants if plant.mill_id == SLICE3_R42_MILL_ID]
        r65 = [plant for plant in loaded.plants if plant.mill_id == SLICE3_R65_MILL_ID]
        r137 = [plant for plant in loaded.plants if plant.mill_id == SLICE3_R137_MILL_ID]
        self.assertEqual(len(r81), 39)
        self.assertEqual(len(r48), 16)
        self.assertEqual(len(r42), 7)
        self.assertEqual(len(r65), 12)
        self.assertEqual(len(r137), 15)
        self.assertEqual([plant.ok.slug for plant in r81], list(EXPECTED_OK_SLUGS))
        self.assertEqual([plant.ok.slug for plant in r48], list(EXPECTED_R48_OK_SLUGS))
        self.assertEqual([plant.ok.slug for plant in r42], list(EXPECTED_R42_OK_SLUGS))
        self.assertEqual([plant.ok.slug for plant in r65], list(EXPECTED_R65_OK_SLUGS))
        self.assertEqual([plant.ok.slug for plant in r137], list(EXPECTED_R137_OK_SLUGS))
        self.assertEqual({plant.shape for plant in r81}, {SHAPE_OK_BAD})
        self.assertEqual(
            {plant.shape for plant in r48 + r42 + r65 + r137},
            {LEFTOVER3_SHAPE},
        )
        self.assertEqual(len({plant.plant_id for plant in loaded.plants}), 89)
        slugs = [plant.ok.slug for plant in loaded.plants] + [
            plant.bad.slug for plant in loaded.plants
        ]
        self.assertEqual(len(set(slugs)), 178)
        self.assertEqual(loaded.meta["source"]["method"], "git-show+ast.parse")
        self.assertEqual(loaded.meta["source"]["commit"], SOURCE_COMMIT)
        self.assertEqual(
            loaded.meta["source"]["scripts"],
            [
                SOURCE_PATH,
                LEFTOVER3_PATH,
                SLICE3_R42_PATH,
                SLICE3_R65_PATH,
                SLICE3_R137_PATH,
            ],
        )
        self.assertEqual(loaded.mills[0].mill_id, SOURCE_MILL_ID)
        self.assertEqual(loaded.mills[0].base_round, SOURCE_ROUND)
        self.assertEqual(loaded.mills[1].mill_id, LEFTOVER3_MILL_ID)
        self.assertEqual(loaded.mills[1].base_round, LEFTOVER3_ROUND)
        self.assertEqual(loaded.mills[2].mill_id, SLICE3_R42_MILL_ID)
        self.assertEqual(loaded.mills[2].base_round, SLICE3_R42_ROUND)
        self.assertEqual(loaded.mills[3].mill_id, SLICE3_R65_MILL_ID)
        self.assertEqual(loaded.mills[3].base_round, SLICE3_R65_ROUND)
        self.assertEqual(loaded.mills[4].mill_id, SLICE3_R137_MILL_ID)
        self.assertEqual(loaded.mills[4].base_round, SLICE3_R137_ROUND)
        self.assertEqual(loaded.plants[0].bad.ticket, "DBF-MEMO-81")
        self.assertEqual(r81[-1].ok.slug, "xlsx-vml-vs-comment")
        self.assertEqual(r48[0].bad.ticket, "ORC-BLOOM-16")
        self.assertEqual(r48[-1].ok.slug, "csv-utf16le-vs-drop")
        self.assertEqual(r42[0].ok.slug, "parquet-footer-vs-drop")
        self.assertEqual(r65[-1].ok.slug, "csv-comment-header-vs-drop")
        self.assertEqual(r137[-1].ok.slug, "capnp-schema-vs-drop")

    def test_fixture_catalog_is_one_pair(self):
        loaded = catalog.load_catalog(FIXTURE)
        self.assertEqual(loaded.catalog_id, "cei-fixture-v1")
        self.assertEqual(len(loaded.plants), 1)
        self.assertEqual(loaded.plants[0].plant_id, "cei_r0001:csv-sniffer-vs-header")
        self.assertEqual(loaded.plants[0].ok.mod, "csvsni")
        self.assertEqual(loaded.plants[0].bad.ticket, "DBF-MEMO-81")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="cei-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(FIXTURE, dest)
        meta_path = dest / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(CeiRefusal) as caught:
            catalog.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_CATALOG_SHA256_MISMATCH)

    def test_unknown_plant_is_a_coded_refusal(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self.assertRaises(CeiRefusal) as caught:
            loaded.plant("cei_r0001:missing")
        self.assertEqual(caught.exception.code, FINDING_PLANT_NOT_FOUND)


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_ok_bad_calls_and_skips_exec(self):
        rows = catalog.plants_from_source(
            TINY_SOURCE, mill_id="cei_r0007", source="tiny_source.py"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["plant_id"], "cei_r0007:tiny-csv-sniffer")
        self.assertEqual(rows[0]["base_round"], 7)
        self.assertEqual(rows[0]["ok"]["domain"], "tiny-csv-sniffer-dialect-index")
        self.assertEqual(rows[0]["bad"]["ticket"], "DBF-TINY-7")
        self.assertIn(rows[0]["ok"]["first_old"], rows[0]["ok"]["src_body"])
        self.assertNotIn("exec", TINY_SOURCE)

    def test_plants_from_source_refuses_a_non_literal_call(self):
        source = "PAIRS = [(_ok(other()), _bad('x'))]\n"
        with self.assertRaises(CeiRefusal) as caught:
            catalog.plants_from_source(source, mill_id="cei_r0001", source="bad.py")
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)

    def test_plants_from_source_reads_leftover3_s_calls_and_skips_exec(self):
        rows = catalog.plants_from_source(
            TINY_LEFTOVER3_SOURCE, mill_id="cei_r0048", source="tiny_leftover3.py"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["plant_id"], "cei_r0048:tiny-parquet-vs-drop")
        self.assertEqual(rows[0]["base_round"], 48)
        self.assertEqual(rows[0]["shape"], LEFTOVER3_SHAPE)
        self.assertEqual(rows[0]["ok"]["wrong"], "os.remove(path)")
        self.assertEqual(rows[0]["bad"]["ticket"], "TINY-ORC-16")
        self.assertNotIn("exec(", TINY_LEFTOVER3_SOURCE)
        self.assertNotIn("hop_unreserved", TINY_LEFTOVER3_SOURCE)

    def test_plants_from_source_refuses_hop_loop_and_foreign_leftover3_importers(self):
        with self.assertRaises(CeiRefusal) as caught:
            catalog.plants_from_source("PAIRS = []\n", mill_id="cei_r81", source="cei-loop-r81.py")
        self.assertEqual(caught.exception.code, FINDING_LOOP_REFUSED)
        with self.assertRaises(CeiRefusal) as caught:
            catalog.plants_from_source(
                "from cei_r48_mill import S, success_ep, fail_ep, notes\nPAIRS = []\n",
                mill_id="cei_r65",
                source="experiments/cei_foreign_leftover3_mill.py",
            )
        self.assertEqual(caught.exception.code, FINDING_LEFTOVER3_EXEC)

    @staticmethod
    def _committed_ok_slugs(mill_id: str) -> list[str]:
        loaded = catalog.load_catalog(COMMITTED)
        return [plant.ok.slug for plant in loaded.plants if plant.mill_id == mill_id]

    def test_slice3_leftover3_mills_parse_without_exec(self):
        for path, mill_id, base_round in (
            (SLICE3_R65_PATH, SLICE3_R65_MILL_ID, SLICE3_R65_ROUND),
            (SLICE3_R137_PATH, SLICE3_R137_MILL_ID, SLICE3_R137_ROUND),
        ):
            text = subprocess.check_output(
                ["git", "show", f"origin/legacy-mill-lane:{path}"],
                cwd=REPO,
                text=True,
            )
            self.assertNotIn("exec(", text)
            rows = catalog.plants_from_source(
                text, mill_id=mill_id, source=path, base_round=base_round
            )
            self.assertGreaterEqual(len(rows), 12)
            extracted_slugs = {row["ok"]["slug"] for row in rows}
            for slug in self._committed_ok_slugs(mill_id):
                self.assertIn(slug, extracted_slugs)

    def test_committed_r42_catalog_matches_legacy_ast(self):
        text = subprocess.check_output(
            ["git", "show", f"origin/legacy-mill-lane:{SLICE3_R42_PATH}"],
            cwd=REPO,
            text=True,
        )
        rows = catalog.plants_from_source(
            text, mill_id=SLICE3_R42_MILL_ID, source=SLICE3_R42_PATH, base_round=SLICE3_R42_ROUND
        )
        r42 = [
            plant
            for plant in catalog.load_catalog(COMMITTED).plants
            if plant.mill_id == SLICE3_R42_MILL_ID
        ]
        self.assertEqual(len(rows), 7)
        self.assertEqual(len(r42), 7)
        for row, plant in zip(rows, r42, strict=True):
            self.assertEqual(row["ok"]["slug"], plant.ok.slug)
            self.assertEqual(row["bad"]["slug"], plant.bad.slug)
            self.assertEqual(row["bad"]["ticket"], plant.bad.ticket)

    def test_committed_catalog_matches_legacy_ast(self):
        try:
            text = subprocess.check_output(
                ["git", "show", f"origin/legacy-mill-lane:{SOURCE_PATH}"],
                cwd=REPO,
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("origin/legacy-mill-lane is not fetched")
        rows = catalog.plants_from_source(
            text, mill_id=SOURCE_MILL_ID, source=SOURCE_PATH, base_round=SOURCE_ROUND
        )
        loaded = catalog.load_catalog(COMMITTED)
        r81 = [plant for plant in loaded.plants if plant.mill_id == SOURCE_MILL_ID]
        self.assertEqual(len(rows), 39)
        self.assertEqual(len(r81), 39)
        for row, plant in zip(rows, r81, strict=True):
            self.assertEqual(row["ok"]["slug"], plant.ok.slug)
            self.assertEqual(row["bad"]["slug"], plant.bad.slug)
            self.assertEqual(row["ok"]["stack"], plant.ok.stack)
            self.assertEqual(row["bad"]["ticket"], plant.bad.ticket)
            self.assertEqual(row["ok"]["first_old"], plant.ok.first_old)
            self.assertEqual(row["ok"]["fix_new"], plant.ok.fix_new)

    def test_committed_r48_catalog_matches_legacy_ast(self):
        try:
            text = subprocess.check_output(
                ["git", "show", f"origin/legacy-mill-lane:{LEFTOVER3_PATH}"],
                cwd=REPO,
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("origin/legacy-mill-lane is not fetched")
        self.assertNotIn("exec(", text)
        rows = catalog.plants_from_source(
            text, mill_id=LEFTOVER3_MILL_ID, source=LEFTOVER3_PATH, base_round=LEFTOVER3_ROUND
        )
        loaded = catalog.load_catalog(COMMITTED)
        r48 = [plant for plant in loaded.plants if plant.mill_id == LEFTOVER3_MILL_ID]
        self.assertEqual(len(rows), 16)
        self.assertEqual(len(r48), 16)
        for row, plant in zip(rows, r48, strict=True):
            self.assertEqual(row["ok"]["slug"], plant.ok.slug)
            self.assertEqual(row["bad"]["slug"], plant.bad.slug)
            self.assertEqual(row["bad"]["ticket"], plant.bad.ticket)
            self.assertEqual(row["ok"]["leftover"], plant.ok.leftover)
            self.assertEqual(row["ok"]["wrong2"], plant.ok.wrong2)

    def test_package_tree_has_no_leftover_mill_scripts(self):
        hits = list((PIPELINES / "cei").rglob("*leftover*_mill.py"))
        self.assertEqual(hits, [])
        self.assertEqual(list((REPO / "config" / "cei").rglob("*leftover*_mill.py")), [])
        self.assertEqual(list((PIPELINES / "cei").rglob("*mill*.py")), [])
        names = tuple(
            sorted(path.name for path in (PIPELINES / "cei").iterdir() if path.suffix == ".py")
        )
        self.assertEqual(
            names, ("__init__.py", "_contract.py", "catalog.py", "cli.py", "generate.py")
        )


class GeneratePairs(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="cei-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_fixture_pair_is_an_episode_and_not_hosted_grok(self):
        dest = self.root / "out"
        request = generate.GenerateRequest(
            FIXTURE, dest, plant_id="cei_r0001:csv-sniffer-vs-header", round=81
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["pairs"], 1)
        self.assertEqual(summary["generator"], GENERATOR)
        self.assertNotEqual(GENERATOR, "grok-4.6")
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        ok, bad = [json.loads(line) for line in lines]
        self.assertEqual(ok["id"], "cei-r81-csv-sniffer-vs-header")
        self.assertEqual(bad["id"], "cei-r81-dbase-memo-handoff")
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(classify_kind(bad), "episode")
        self.assertEqual(mill_prefix(ok), "cei")
        self.assertEqual(mill_prefix(bad), "cei")
        self.assertFalse(ok["id"].startswith("sir-"))
        self.assertFalse(ok["id"].startswith("dbc-"))
        self.assertTrue(ok["reward"]["success"])
        self.assertFalse(bad["reward"]["success"])
        self.assertEqual(len(ok["steps"]), 16)
        self.assertEqual(len(bad["steps"]), 17)
        self.assertEqual(ok["meta"]["factory"], FACTORY)
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertNotEqual(ok["meta"]["generator"], "grok-4.6")
        self.assertEqual(ok["steps"][0]["decision_basis"][:5], "Plan:")
        notes = (dest / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        self.assertIn("Novel coverage: 84%", notes)
        self.assertIn(GENERATOR, notes)
        self.assertNotIn("grok-4.6", notes)

    def test_leftover3_pair_is_an_episode_and_not_hosted_grok(self):
        dest = self.root / "leftover3-out"
        request = generate.GenerateRequest(
            COMMITTED, dest, plant_id="cei_r48:parquet-columnindex-vs-drop"
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["pairs"], 1)
        self.assertEqual(summary["generator"], GENERATOR)
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        ok, bad = [json.loads(line) for line in lines]
        self.assertEqual(ok["id"], "cei-r48-parquet-columnindex-vs-drop")
        self.assertEqual(bad["id"], "cei-r48-orc-bloom-vs-drop")
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(classify_kind(bad), "episode")
        self.assertEqual(mill_prefix(ok), "cei")
        self.assertTrue(ok["reward"]["success"])
        self.assertFalse(bad["reward"]["success"])
        self.assertEqual(len(ok["steps"]), 16)
        self.assertEqual(len(bad["steps"]), 17)
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertNotEqual(ok["meta"]["generator"], "grok-4.6")
        self.assertIn("bind leftover", ok["steps"][12]["observation"])
        self.assertEqual(bad["meta"]["round"], 48)
        notes = (dest / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        self.assertIn("Novel coverage: 84%", notes)
        self.assertIn("leftover leftover leftover", notes)
        self.assertIn(GENERATOR, notes)
        self.assertNotIn("grok-4.6", notes)
        self.assertNotIn("hop_unreserved", notes)

    def test_default_round_is_catalog_first_plus_index(self):
        dest = self.root / "default-round"
        generate.run(
            generate.GenerateRequest(FIXTURE, dest, plant_id="cei_r0001:csv-sniffer-vs-header")
        )
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        ok = json.loads(lines[0])
        self.assertEqual(ok["id"], "cei-r1-csv-sniffer-vs-header")
        self.assertEqual(ok["meta"]["round"], 1)

    def test_existing_destination_is_refused(self):
        dest = self.root / "exists"
        dest.mkdir()
        with self.assertRaises(CeiRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_EXISTS)

    def test_destination_under_raw_is_refused(self):
        dest = self.root / "outputs" / "raw" / "cei-out"
        with self.assertRaises(CeiRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(dest.exists())

    def test_generate_requires_exactly_one_selector(self):
        dest = self.root / "none"
        with self.assertRaises(CeiRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest))
        self.assertEqual(caught.exception.code, FINDING_USAGE)


class CliSurface(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="cei-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_check_json_on_the_fixture(self):
        code, out, err = invoke(["catalog-check", "--catalog", str(FIXTURE), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 1)
        self.assertEqual(payload["findings"], [])

    def test_catalog_json_lists_the_fixture_pair(self):
        code, out, err = invoke(["catalog", "--catalog", str(FIXTURE), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["plants"][0]["ok"], "csv-sniffer-vs-header")
        self.assertEqual(payload["plants"][0]["ticket"], "DBF-MEMO-81")

    def test_generate_json_writes_the_pair(self):
        dest = self.root / "cli-out"
        code, out, err = invoke(
            [
                "generate",
                "--catalog",
                str(FIXTURE),
                "--out",
                str(dest),
                "--plant",
                "cei_r0001:csv-sniffer-vs-header",
                "--json",
            ]
        )
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 2)
        self.assertTrue((dest / generate.RECORDS_FILENAME).is_file())

    def test_missing_catalog_is_exit_two_and_json_on_stdout(self):
        code, out, err = invoke(["catalog-check", "--catalog", "/nonexistent/cei", "--json"])
        self.assertEqual((code, err), (2, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "refused")
        self.assertTrue(payload["code"].startswith("cei."))


class ImportTwins(unittest.TestCase):
    def test_flat_and_package_catalog_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        import pipelines.cei.catalog as packaged

        self.assertIs(packaged, catalog)


if __name__ == "__main__":
    unittest.main()
