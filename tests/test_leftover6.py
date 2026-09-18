#!/usr/bin/env python3
"""FAMILY=leftover6: AST catalog extract of leftover6 mills (no vendored publishers)."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pipelines.leftover6 import (
    CATALOG,
    CatalogError,
    extract_source,
    is_vendor_filename,
    load_catalog,
    refuse_vendor_paths,
)
from pipelines.leftover6 import catalog as leftover6_catalog
from pipelines.leftover6.catalog_extract import (
    GQL_PATH,
    SBOX_PATH,
    SSL_PATH,
    UNSET,
    dumps_jsonl,
    literal_value,
)
from pipelines.mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "pipelines" / "leftover6"
CONFIG_DIR = ROOT / "config" / "leftover6"
CATALOG_JSON = CONFIG_DIR / "CATALOG.json"
PAIRS_JSONL = CONFIG_DIR / "pairs.jsonl"
PLANTS_JSONL = CONFIG_DIR / "plants.jsonl"

_GQL_SNIPPET = """
FAC = "graphql-nplusone-factory"
GEN = "grok-4.6"
PAIRS = [
    dict(
        slug="dl-batch-dispatch-bind",
        fail="dl-drop-cachekey-handoff",
        surf="DataLoader leftover leftover leftover leftover leftover leftover batch",
        naive="disable batch",
        bind="dispatch this tick's keys only",
        drop="cacheKeyFn",
        plant="quoin-batch",
        file="src/quoinBatch.ts",
        test="tests/test_quoin_batch.py",
        field="quoinPull",
        ticket="GQL-L6-260",
    ),
]
"""

_PUBLISHER_NAMES = frozenset(
    {"build_success", "build_partial", "candidates", "try_reserve", "run_one", "main"}
)


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", f"origin/legacy-mill-lane:{GQL_PATH}"],
            cwd=ROOT,
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


class Leftover6CatalogTests(unittest.TestCase):
    def test_reviewed_homes_stay_on_source_prefixes(self):
        self.assertNotIn("leftover6", REVIEWED_MILL_PREFIX_HOMES)
        self.assertEqual(leftover6_catalog.FAMILY, "leftover6")
        homes = {mill.reviewed_prefix: mill.factory for mill in CATALOG.catalogs}
        self.assertEqual(homes["gql"], REVIEWED_MILL_PREFIX_HOMES["gql"])
        self.assertEqual(homes["sbox"], REVIEWED_MILL_PREFIX_HOMES["sbox"])
        self.assertEqual(homes["ssl"], REVIEWED_MILL_PREFIX_HOMES["ssl"])

    def test_three_leftover6_sources_are_committed_in_full(self):
        self.assertEqual(len(CATALOG.catalogs), 3)
        self.assertEqual(CATALOG.n_pair_rows, 32)
        self.assertEqual(CATALOG.n_plant_rows, 65)
        self.assertEqual(CATALOG.slice, "full")
        self.assertEqual(CATALOG.source_commit, leftover6_catalog.SOURCE_COMMIT)
        gql, ssl, sbox = CATALOG.catalogs
        self.assertEqual(gql.source_path, GQL_PATH)
        self.assertEqual(ssl.source_path, SSL_PATH)
        self.assertEqual(sbox.source_path, SBOX_PATH)
        self.assertEqual(gql.n_rows, 16)
        self.assertEqual(ssl.n_rows, 16)
        self.assertEqual(sbox.n_rows, 65)
        self.assertEqual(gql.first_slug, "dl-batch-dispatch-bind")
        self.assertEqual(gql.last_slug, "nexus-plugin-bind")
        self.assertEqual(ssl.first_slug, "step-ca-mintls-leftover6-bind")
        self.assertEqual(ssl.last_slug, "cert-manager-revision-leftover6-bind")
        self.assertEqual(sbox.first_slug, "leftover-openvms-sda")
        self.assertEqual(sbox.last_slug, "leftover-jailhouse-cell")
        self.assertEqual(gql.source_blob_sha1, "a6d222886ca88c8fadce462ef46dabce54fd7419")
        self.assertEqual(ssl.source_blob_sha1, "95eff73e6700db77379060471b7fdd0c8fcf3e70")
        self.assertEqual(sbox.source_blob_sha1, "c321f3ea9d9e87d514c4d75b8470addff3a421ca")

    def test_no_vendored_leftover6_mills(self):
        hits = []
        for pattern in leftover6_catalog.FORBIDDEN_MILL_GLOBS:
            hits.extend(
                path
                for path in ROOT.rglob(pattern)
                if "legacy-mill-lane" not in str(path)
                and ".git" not in path.parts
            )
        self.assertEqual(hits, [])
        self.assertTrue(is_vendor_filename("mill_gql_leftover6_r260.py"))
        self.assertTrue(is_vendor_filename("ssl_r164_leftover6_mill.py"))
        self.assertTrue(is_vendor_filename("sbox-mill-plants-leftover6.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/mill_gql_leftover6_r260.py")])

    def test_extractor_modules_never_exec(self):
        hits = []
        for name in ("catalog_extract.py", "catalog.py", "__init__.py"):
            hits.extend(_module_uses_exec(PACKAGE / name))
        self.assertEqual(hits, [])

    def test_package_has_no_launderer_publishers(self):
        names: set[str] = set()
        for path in PACKAGE.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.add(node.name)
        self.assertEqual(names & _PUBLISHER_NAMES, set())
        self.assertFalse((PACKAGE / "generate.py").exists())
        self.assertFalse((PACKAGE / "cli.py").exists())

    def test_extractor_reads_literal_gql_dict_pairs(self):
        extracted = extract_source(
            _GQL_SNIPPET,
            path="experiments/mill_gql_leftover6_r260.py",
        )
        self.assertEqual(extracted["shape"], "dict-kwargs")
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "dl-batch-dispatch-bind")
        self.assertEqual(extracted["rows"][0]["fail"], "dl-drop-cachekey-handoff")
        self.assertEqual(extracted["rows"][0]["round"], 260)
        self.assertEqual(extracted["factory"], "graphql-nplusone-factory")

    def test_extractor_refuses_non_literal_pairs(self):
        source = "FAC = 'graphql-nplusone-factory'\nGEN = 'grok-4.6'\nPAIRS = [leftover_pair()]\n"
        with self.assertRaises(ValueError):
            extract_source(source, path="experiments/mill_gql_leftover6_r260.py")

    def test_extractor_refuses_a_nonliteral_reassignment(self):
        source = _GQL_SNIPPET + "\nPAIRS = rebuild_pairs()\n"
        with self.assertRaises(ValueError):
            extract_source(source, path="experiments/mill_gql_leftover6_r260.py")

    def test_extractor_refuses_duplicate_keywords_and_unhashable_mapping_keys(self):
        duplicate_keywords = ast.parse("dict(slug='first', slug='second')").body[0].value
        unhashable_key = ast.parse("{['key']: 'value'}").body[0].value
        self.assertIs(literal_value(duplicate_keywords), UNSET)
        self.assertIs(literal_value(unhashable_key), UNSET)

    def test_catalog_modules_keep_direct_and_packaged_import_identity(self):
        program = """
import importlib
import sys
from pathlib import Path
root = Path.cwd()
sys.path.insert(0, str(root / 'pipelines'))
first = importlib.import_module(sys.argv[1])
second = importlib.import_module(sys.argv[2])
if first is not second or first.CatalogError is not second.CatalogError:
    raise SystemExit('leftover6 import identity diverged')
"""
        for first, second in (
            ("leftover6.catalog", "pipelines.leftover6.catalog"),
            ("pipelines.leftover6.catalog", "leftover6.catalog"),
        ):
            with self.subTest(first=first):
                subprocess.run(
                    [sys.executable, "-c", program, first, second],
                    cwd=ROOT,
                    check=True,
                )

    def test_jsonl_stays_compact(self):
        for path, expected in ((PAIRS_JSONL, 32), (PLANTS_JSONL, 65)):
            text = path.read_text(encoding="utf-8")
            lines = text.splitlines()
            self.assertEqual(len(lines), expected, path.name)
            self.assertTrue(text.endswith("\n"))
            self.assertNotIn("\r", text)
            for line in lines:
                self.assertFalse(line.startswith((" ", "\t")))
                json.loads(line)

    def test_loader_fails_closed_on_a_missing_case_field(self):
        header = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        lines = PAIRS_JSONL.read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        del first["ticket"]
        lines[0] = json.dumps(first, separators=(",", ":"))
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            (dest / "pairs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            (dest / "plants.jsonl").write_text(PLANTS_JSONL.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(CatalogError, "keys differ"):
                load_catalog(dest)

    def test_loader_refuses_a_wrong_pair_value_type(self):
        header = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        lines = PAIRS_JSONL.read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        first["round"] = "260"
        lines[0] = json.dumps(first, separators=(",", ":"))
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            (dest / "pairs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            (dest / "plants.jsonl").write_text(PLANTS_JSONL.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(CatalogError, "round must be an integer"):
                load_catalog(dest)

    def test_loader_refuses_a_non_string_pair_kind(self):
        header = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        rows = [json.loads(line) for line in PAIRS_JSONL.read_text(encoding="utf-8").splitlines()]
        rows[0]["kind"] = []
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            (dest / "pairs.jsonl").write_text(dumps_jsonl(rows), encoding="utf-8")
            (dest / "plants.jsonl").write_text(PLANTS_JSONL.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(CatalogError, "kind is not a leftover6 pair"):
                load_catalog(dest)

    def test_loader_refuses_duplicate_json_keys_and_non_lf_framing(self):
        header = CATALOG_JSON.read_bytes()
        pairs = PAIRS_JSONL.read_bytes()
        plants = PLANTS_JSONL.read_bytes()
        duplicate = pairs.replace(b'"kind":"gql-pairs"', b'"kind":"gql-pairs","kind":"gql-pairs"', 1)
        for label, candidate, expected in (
            ("duplicate", duplicate, "duplicate JSON object key"),
            ("crlf", pairs.replace(b"\n", b"\r\n"), "carriage returns"),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                dest = Path(temp_dir)
                (dest / "CATALOG.json").write_bytes(header)
                (dest / "pairs.jsonl").write_bytes(candidate)
                (dest / "plants.jsonl").write_bytes(plants)
                with self.assertRaisesRegex(CatalogError, expected):
                    load_catalog(dest)

    def test_loader_keeps_unicode_line_separator_inside_a_json_string(self):
        header = CATALOG_JSON.read_bytes()
        pairs = PAIRS_JSONL.read_bytes().replace(
            b'"fail":"dl-drop-cachekey-handoff"',
            b'"fail":"dl-drop\\u2028cachekey-handoff"',
            1,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_bytes(header)
            (dest / "pairs.jsonl").write_bytes(pairs)
            (dest / "plants.jsonl").write_bytes(PLANTS_JSONL.read_bytes())
            self.assertEqual(load_catalog(dest).pairs[0]["fail"], "dl-drop\u2028cachekey-handoff")

    def test_loader_refuses_stale_declared_totals(self):
        header = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        header["n_pair_rows_committed"] += 1
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            (dest / "pairs.jsonl").write_text(PAIRS_JSONL.read_text(encoding="utf-8"))
            (dest / "plants.jsonl").write_text(PLANTS_JSONL.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(CatalogError, "n_pair_rows_committed"):
                load_catalog(dest)

    def test_loader_refuses_duplicate_or_gapped_pair_rows(self):
        header = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        rows = [json.loads(line) for line in PAIRS_JSONL.read_text(encoding="utf-8").splitlines()]
        rows[1]["slug"] = rows[0]["slug"]
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            (dest / "pairs.jsonl").write_text(dumps_jsonl(rows), encoding="utf-8")
            (dest / "plants.jsonl").write_text(PLANTS_JSONL.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(CatalogError, "duplicate identities"):
                load_catalog(dest)
        rows[1]["slug"] = "unique-test-slug"
        rows[1]["round"] += 1
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            (dest / "pairs.jsonl").write_text(dumps_jsonl(rows), encoding="utf-8")
            (dest / "plants.jsonl").write_text(PLANTS_JSONL.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(CatalogError, "not contiguous"):
                load_catalog(dest)


class Leftover6LegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        pair_rows = []
        plant_rows = []
        for mill in CATALOG.catalogs:
            text = subprocess.check_output(
                ["git", "show", f"{mill.preserve_commit}:{mill.source_path}"],
                text=True,
                cwd=ROOT,
            )
            blob = subprocess.check_output(
                ["git", "rev-parse", f"{mill.preserve_commit}:{mill.source_path}"],
                text=True,
                cwd=ROOT,
            ).strip()
            self.assertEqual(blob, mill.source_blob_sha1, mill.source_path)
            live = extract_source(text, path=mill.source_path, blob_sha=blob)
            self.assertEqual(live["n_rows"], mill.n_rows, mill.source_path)
            self.assertEqual(live["first_slug"], mill.first_slug, mill.source_path)
            self.assertEqual(live["last_slug"], mill.last_slug, mill.source_path)
            self.assertEqual(live["sha256"], mill.source_sha256, mill.source_path)
            self.assertEqual(live["shape"], mill.shape, mill.source_path)
            if live["kind"] == "sbox-plants":
                plant_rows.extend({"source_path": mill.source_path, **row} for row in live["rows"])
            else:
                pair_rows.extend({"source_path": mill.source_path, **row} for row in live["rows"])
        self.assertEqual(dumps_jsonl(pair_rows), PAIRS_JSONL.read_text(encoding="utf-8"))
        self.assertEqual(dumps_jsonl(plant_rows), PLANTS_JSONL.read_text(encoding="utf-8"))

    def test_git_show_is_the_only_legacy_read(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            refuse_vendor_paths(dest.rglob("*") if dest.exists() else ())
            self.assertEqual(list(dest.glob("*leftover6*")), [])


if __name__ == "__main__":
    unittest.main()
