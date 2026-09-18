#!/usr/bin/env python3
"""PR-a/PR-b: AST catalog extract, skeleton, and deferred ``pairs.jsonl``."""

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

from azr.catalog import CATALOG, load_catalog  # noqa: E402
from azr.catalog_extract import (  # noqa: E402
    SHAPE_IDOR_BFLA,
    SHAPE_IDOR_BFLA_COMPOSE,
    SHAPE_LITERAL,
    SHAPE_NEW_PLUS_KEEP,
    SHAPE_PLANTS_ZIP,
    SHAPE_SLICE,
    catalog_document,
    catalog_json_path,
    deferred_pair_rows,
    dumps_catalog,
    dumps_pairs_jsonl,
    extract_companion_path,
    extract_mill_catalog,
    extract_plant_catalog,
    mill_summary,
    pair_identity,
    pairs_jsonl_path,
)
from azr.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from azr.sources import (  # noqa: E402
    MILL_SOURCES,
    catalog_sources,
    gen_sources,
    loop_sources,
    plant_sources,
)
from azr import vocabulary as av  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_R1181_SNIPPET = """
FACTORY = "authz-regression-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 1181
PAIRS: list[tuple[dict, dict]] = [
    (
        {"slug": "keep-a", "plant": "capstan"},
        {"slug": "keep-a-fail", "plant": "capstan"},
    ),
    (
        {"slug": "keep-b", "plant": "davit"},
        {"slug": "keep-b-fail", "plant": "davit"},
    ),
]
"""

_R1193_SNIPPET = """
FACTORY = "authz-regression-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 1193
KEEP_FROM_UNUSED = {
    "jackson-isadmin-missing-jsonignore",
    "opa-classification-default-public",
}

def jackson_opa_pair():
    for pair in ():
        if pair[0]["slug"] == "jackson-isadmin-missing-jsonignore":
            return pair
    raise SystemExit("missing")

NEW_PAIRS: list[tuple[dict, dict]] = [
    (
        {"slug": "invoice-number-global-lookup-idor", "plant": "lanyard"},
        {"slug": "casbin-grouping-after-leave", "plant": "lanyard"},
    ),
]
"""

_R1205_SNIPPET = """
FACTORY = "authz-regression-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 1205

def _bflas():
    out = []
    def add(spec):
        out.append(spec)
    add(dict(slug="flask-blueprint-delete-unguarded", plant="hawse"))
    return out

IDOR_ROWS = [
    dict(slug="vin-vehicle-title-idor", plant="hawse"),
]
"""

_PLANT_SNIPPET = """
EXTRA_IDOR_ROWS = [
    dict(slug="mgrs-grid-idor", plant="abeam"),
    dict(slug="maidenhead-grid-idor", plant="adrift"),
]

def extra_bflas(H):
    rows = []
    def add(**kw):
        rows.append(H(**kw))
    add(slug="loopback-remote-skip-delete", plant="abeam")
    add(slug="other-skip-delete", plant="adrift")
    return rows
"""

_ZIP_SNIPPET = """
FACTORY = "authz-regression-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 1365
import importlib.util
_plants_spec = importlib.util.spec_from_file_location(
    "azr_plants_r1365", EXPERIMENTS / "azr-plants-r1365.py"
)
if PAIRS[0][0]["slug"] != "mgrs-grid-idor":
    raise SystemExit("bad")
if PAIRS[0][1]["slug"] != "loopback-remote-skip-delete":
    raise SystemExit("bad")
"""

_SLICE_SNIPPET = """
FACTORY = "authz-regression-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 1285
_OFFSET = CATALOG_FIRST - 1205
PAIRS = OTHER.PAIRS[_OFFSET:]
if PAIRS[0][0]["slug"] != "icd10-dx-idor":
    raise SystemExit("bad")
if PAIRS[0][1]["slug"] != "litestar-skip-guard-delete":
    raise SystemExit("bad")
"""


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", "origin/legacy-mill-lane:experiments/azr-mill-r1181.py"],
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


def _show(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{av.LEGACY_REF}:{path}"],
        text=True,
        cwd=REPO,
    )


def _plant_texts() -> dict[str, str]:
    return {source.path: _show(source.path) for source in plant_sources()}


class AzrSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[av.FAMILY_PREFIX], av.FACTORY)
        self.assertEqual(av.FACTORY, "authz-regression-factory")
        self.assertEqual(av.GENERATOR, "grok-4.6")
        self.assertEqual(av.PRESERVE_COMMIT, "9e7fe52231c94b8a9fd3e5b28995505651dbb37e")

    def test_seventy_six_sources_split(self):
        self.assertEqual(len(MILL_SOURCES), 76)
        self.assertEqual(len(catalog_sources()), 22)
        self.assertEqual(len(loop_sources()), 22)
        self.assertEqual(len(plant_sources()), 20)
        self.assertEqual(len(gen_sources()), 12)
        self.assertEqual(
            {source.companion_path for source in loop_sources()},
            {f"experiments/azr-mill-{suffix}" for suffix in _loop_suffixes()},
        )

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in av.FORBIDDEN_MILL_GLOBS:
            hits.extend(path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path))
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("azr-mill-r1181.py"))
        self.assertTrue(is_vendor_filename("azr-loop-r1181.py"))
        self.assertTrue(is_vendor_filename("azr-plants-r1365.py"))
        self.assertTrue(is_vendor_filename("_gen_azr_plants_r1365.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/azr-mill-r1181.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "azr"
        hits = []
        for name in ("catalog_ast.py", "catalog_extract.py", "catalog.py", "identity.py"):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_extractor_reads_literal_pairs(self):
        extracted = extract_mill_catalog(_R1181_SNIPPET, path="experiments/azr-mill-r1181.py")
        self.assertEqual(extracted["shape"], SHAPE_LITERAL)
        self.assertEqual(extracted["catalog_first"], 1181)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "keep-a")
        self.assertEqual(extracted["last_slug"], "keep-b")
        self.assertEqual(extracted["pairs"][0]["success_plant"], "capstan")

    def test_extractor_reads_new_plus_keep(self):
        extracted = extract_mill_catalog(_R1193_SNIPPET, path="experiments/azr-mill-r1193.py")
        self.assertEqual(extracted["shape"], SHAPE_NEW_PLUS_KEEP)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "jackson-isadmin-missing-jsonignore")
        self.assertEqual(extracted["first_fail_slug"], "opa-classification-default-public")
        self.assertEqual(extracted["last_slug"], "invoice-number-global-lookup-idor")

    def test_extractor_reads_idor_bfla_rows(self):
        extracted = extract_mill_catalog(_R1205_SNIPPET, path="experiments/azr-mill-r1205.py")
        self.assertEqual(extracted["shape"], SHAPE_IDOR_BFLA)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "vin-vehicle-title-idor")
        self.assertEqual(extracted["first_fail_slug"], "flask-blueprint-delete-unguarded")

    def test_extractor_reads_plant_rows(self):
        extracted = extract_plant_catalog(_PLANT_SNIPPET, path="experiments/azr-plants-r1365.py")
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "mgrs-grid-idor")
        self.assertEqual(extracted["first_fail_slug"], "loopback-remote-skip-delete")

    def test_extractor_zips_companion_plant(self):
        extracted = extract_mill_catalog(
            _ZIP_SNIPPET,
            path="experiments/azr-mill-r1365.py",
            plants={"experiments/azr-plants-r1365.py": _PLANT_SNIPPET},
        )
        self.assertEqual(extracted["shape"], SHAPE_PLANTS_ZIP)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "mgrs-grid-idor")
        self.assertEqual(extracted["last_slug"], "maidenhead-grid-idor")
        self.assertEqual(extracted["companion_path"], "experiments/azr-plants-r1365.py")

    def test_extractor_reads_slice_tips(self):
        extracted = extract_mill_catalog(_SLICE_SNIPPET, path="experiments/azr-mill-r1285.py")
        self.assertEqual(extracted["shape"], SHAPE_SLICE)
        self.assertEqual(extracted["first_slug"], "icd10-dx-idor")
        self.assertEqual(extracted["first_fail_slug"], "litestar-skip-guard-delete")

    def test_loop_mill_path_constant(self):
        source = (
            "ROOT = Path(__file__).resolve().parents[1]\n"
            'MILL = ROOT / "experiments" / "azr-mill-r1181.py"\n'
        )
        self.assertEqual(extract_companion_path(source), "experiments/azr-mill-r1181.py")

    def test_gen_out_with_name(self):
        source = 'OUT = Path(__file__).with_name("azr-plants-r1365.py")\n'
        self.assertEqual(extract_companion_path(source), "experiments/azr-plants-r1365.py")

    def test_leftover3_loop_spec_path(self):
        source = (
            "ROOT = Path(__file__).resolve().parents[1]\n"
            "spec = importlib.util.spec_from_file_location(\n"
            '    "azr_mill_r1415", ROOT / "experiments" / "azr-mill-r1415-leftover3.py"\n'
            ")\n"
        )
        self.assertEqual(extract_companion_path(source), "experiments/azr-mill-r1415-leftover3.py")

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 22)
        self.assertEqual(CATALOG.n_pair_rows, 1333)
        self.assertEqual(CATALOG.slice, "r1181")
        self.assertEqual(CATALOG.preserve_commit, av.PRESERVE_COMMIT)
        r1181 = CATALOG.mills["azr-mill-r1181"]
        self.assertEqual(r1181.n_rows, 13)
        self.assertEqual(r1181.catalog_first, 1181)
        self.assertEqual(r1181.first_slug, "nested-path-memo-id-ignored-org")
        self.assertEqual(r1181.last_slug, "jackson-isadmin-missing-jsonignore")
        self.assertEqual(len(r1181.pairs), 13)
        self.assertEqual(r1181.pairs[0]["fail_slug"], "openfga-unshare-write-not-delete")
        self.assertEqual(CATALOG.n_deferred_pair_rows, av.DEFERRED_PAIR_ROWS)
        bulky = CATALOG.mills[av.BULKY_MILL_ID]
        self.assertEqual(bulky.n_rows, av.BULKY_N_ROWS)
        self.assertEqual(len(bulky.pairs), av.BULKY_N_ROWS)
        self.assertEqual(CATALOG.mills["azr-mill-r1193"].n_rows, 12)
        self.assertEqual(CATALOG.mills["azr-mill-r1205"].n_rows, 160)
        self.assertEqual(CATALOG.mills["azr-mill-r1205"].shape, SHAPE_IDOR_BFLA_COMPOSE)
        self.assertEqual(CATALOG.mills["azr-mill-r1245"].n_rows, 20)
        self.assertEqual(CATALOG.mills["azr-mill-r1285"].first_slug, "icd10-dx-idor")
        self.assertEqual(CATALOG.mills["azr-mill-r1365"].first_slug, "mgrs-grid-idor")
        self.assertEqual(len(CATALOG.mills["azr-mill-r2320"].pairs), 80)

    def test_header_omits_deferred_pair_bodies(self):
        header = json.loads(catalog_json_path().read_text(encoding="utf-8"))
        self.assertEqual(header["slice"], av.SLICE_ID)
        self.assertEqual(header["n_pair_rows"], 1333)
        for mill_id, row in header["mills"].items():
            if mill_id == av.SLICE_MILL_ID:
                self.assertEqual(len(row["pairs"]), 13)
            else:
                self.assertNotIn("pairs", row, mill_id)

    def test_pairs_jsonl_stays_compact(self):
        path = pairs_jsonl_path()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), av.DEFERRED_PAIR_ROWS)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        parsed = []
        seen = set()
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            row = json.loads(line)
            self.assertEqual(set(row), set(av.PAIR_ROW_KEYS))
            key = (row["mill_id"], row["success_slug"])
            self.assertNotIn(key, seen)
            seen.add(key)
            parsed.append(row)
        self.assertNotIn(av.SLICE_MILL_ID, {row["mill_id"] for row in parsed})
        bulky_rows = [row for row in parsed if row["mill_id"] == av.BULKY_MILL_ID]
        self.assertEqual(len(bulky_rows), av.BULKY_N_ROWS)
        self.assertEqual(bulky_rows[0]["success_slug"], "vin-vehicle-title-idor")
        self.assertEqual(bulky_rows[-1]["success_slug"], "geohash-cell-idor")

    def test_loader_fails_closed_on_a_missing_pair_field(self):
        header = catalog_json_path().read_text(encoding="utf-8")
        lines = pairs_jsonl_path().read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        del first["success_slug"]
        lines[0] = json.dumps(first, separators=(",", ":"))
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_text(header, encoding="utf-8")
            (dest / "pairs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "keys differ"):
                load_catalog(dest / "CATALOG.json")


def _loop_suffixes() -> set[str]:
    return {
        "r1181.py",
        "r1193.py",
        "r1205.py",
        "r1245.py",
        "r1285.py",
        "r1365.py",
        "r1415-leftover3.py",
        "r1464.py",
        "r1504.py",
        "r1506-leftover3.py",
        "r1544-leftover3.py",
        "r1544.py",
        "r1640.py",
        "r1720.py",
        "r1760.py",
        "r1840.py",
        "r1920.py",
        "r2000.py",
        "r2080.py",
        "r2160.py",
        "r2240.py",
        "r2320.py",
    }


class AzrLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        plants = _plant_texts()
        mills = []
        extracts = []
        for source in catalog_sources():
            text = _show(source.path)
            blob = subprocess.check_output(
                ["git", "rev-parse", f"{av.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            ).strip()
            self.assertEqual(blob, source.blob_sha, source.mill_id)
            live = extract_mill_catalog(
                text,
                path=source.path,
                blob_sha=source.blob_sha,
                plants=plants,
            )
            committed = CATALOG.mills[source.mill_id]
            self.assertEqual(live["n_rows"], committed.n_rows, source.mill_id)
            self.assertEqual(live["first_slug"], committed.first_slug, source.mill_id)
            self.assertEqual(live["last_slug"], committed.last_slug, source.mill_id)
            self.assertEqual(live["catalog_first"], committed.catalog_first, source.mill_id)
            self.assertEqual(live["sha256"], committed.sha256, source.mill_id)
            self.assertEqual(live["shape"], committed.shape, source.mill_id)
            self.assertEqual(
                [pair_identity(pair) for pair in live["pairs"]],
                list(committed.pairs),
                source.mill_id,
            )
            extracts.append(live)
            mills.append(mill_summary(live, include_pairs=source.mill_id == av.SLICE_MILL_ID))
        self.assertEqual(
            dumps_catalog(catalog_document(mills)),
            catalog_json_path().read_text(encoding="utf-8"),
        )
        self.assertEqual(
            dumps_pairs_jsonl(deferred_pair_rows(extracts)),
            pairs_jsonl_path().read_text(encoding="utf-8"),
        )

    def test_loop_and_gen_scripts_name_companions(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        for source in (*loop_sources(), *gen_sources()):
            text = _show(source.path)
            self.assertEqual(
                extract_companion_path(text),
                source.companion_path,
                source.mill_id,
            )

    def test_git_show_is_the_only_legacy_read(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            refuse_vendor_paths(dest.rglob("*") if dest.exists() else ())
            self.assertEqual(list(dest.glob("azr-mill*.py")), [])


if __name__ == "__main__":
    unittest.main()
