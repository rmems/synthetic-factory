#!/usr/bin/env python3
"""DBC catalog extract: PR-a skeleton plus the deferred ``pairs.jsonl`` slice."""

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

from dbc.catalog import CATALOG, load_pairs_jsonl  # noqa: E402
from dbc.catalog_extract import (  # noqa: E402
    SHAPE_CTOR,
    SHAPE_LEFTOVER_LANG,
    SHAPE_LITERAL,
    SHAPE_PLANT_BUILD,
    SHAPE_SKIP_EXTRA,
    SHAPE_ZIP_TABLES,
    catalog_document,
    catalog_json_path,
    compose_family_records,
    deferred_pair_rows,
    dumps_catalog,
    dumps_pairs_jsonl,
    extract_companion_path,
    extract_mill_catalog,
    mill_summary,
    pairs_jsonl_path,
    sha256_bytes,
)
from dbc.identity import (  # noqa: E402
    is_excluded_launderer_path,
    is_vendor_filename,
    refuse_vendor_paths,
)
from dbc.sources import (  # noqa: E402
    EXCLUDED_LAUNDERERS,
    MILL_SOURCES,
    catalog_sources,
    gen_sources,
    hop_sources,
    loop_sources,
)
from dbc import vocabulary as cv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_LITERAL_SNIPPET = """
FACTORY = "docker-build-cache-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 193
PAIRS: list[tuple[dict, dict]] = [
    (
        {"slug": "keep-a", "harbor": "harbor-a"},
        {"slug": "keep-a-left", "harbor": "harbor-a-jobs"},
    ),
    (
        {"slug": "keep-b", "harbor": "harbor-b"},
        {"slug": "keep-b-left", "harbor": "harbor-b-jobs"},
    ),
]
"""

_SKIP_EXTRA_SNIPPET = """
SKIP = {"drop-me", "drop-me-left"}
EXTRA = [
    (
        {"slug": "extra-a", "harbor": "harbor-x"},
        {"slug": "extra-a-left", "harbor": "harbor-x-jobs"},
    ),
]
PAIRS = [p for p in _r233.PAIRS if p[0]["slug"] not in SKIP and p[1]["slug"] not in SKIP] + EXTRA
"""

_CTOR_SNIPPET = """
PAIRS = [
    (
        suc(slug="buf-mod-cache", harbor="harbor-buf"),
        left(slug="softlockup-leftover", harbor="harbor-softlock"),
    ),
]
"""

_ZIP_SNIPPET = """
_CRYPTO = [("botan-cache", "BOTAN_HOME"), ("wolfssl-cache", "WOLFSSL_HOME")]
_GPIO = [("gpio-amd-leftover", "GPIO_AMD"), ("gpio-pch-leftover", "GPIO_PCH")]
PAIRS = []
for i, (c, g) in enumerate(zip(_CRYPTO, _GPIO)):
    PAIRS.append((_mk_lang(c, "sib"), _mk_left(g, "sib")))
"""

_LEFTOVER_LANG_SNIPPET = """
LANGS = [{"slug": "racket-collects-cache", "lang": "racket"}]
LEFTOVERS = [{"slug": "zonefs-cnv-leftover", "kind": "zonefs"}]
PAIRS = list(zip(LANGS, LEFTOVERS))
"""

_PLANT_SNIPPET = """
def build(lang, left):
    L, R = lang, left
    return [
        (
            L("namd-charm-cache", "harbor-namd"),
            R(slug="fat-utf8-leftover", harbor="harbor-fatutf"),
        ),
    ]
"""


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", f"{cv.LEGACY_REF}:experiments/dbc-mill-r193.py"],
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


class DbcSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FACTORY, "docker-build-cache-factory")
        self.assertEqual(cv.GENERATOR, "grok-4.6")
        self.assertEqual(cv.PRESERVE_COMMIT, "b183a48c94892a71d543321acc808129dc399e50")

    def test_sixty_seven_included_sources_exclude_launderers(self):
        self.assertEqual(len(MILL_SOURCES), 67)
        self.assertEqual(len(catalog_sources()), 32)
        self.assertEqual(len(loop_sources()), 27)
        self.assertEqual(len(gen_sources()), 3)
        self.assertEqual(len(hop_sources()), 4)
        self.assertEqual(len(EXCLUDED_LAUNDERERS), 2)
        self.assertEqual(
            {source.path for source in EXCLUDED_LAUNDERERS},
            set(cv.EXCLUDED_LAUNDERER_PATHS),
        )
        catalog_paths = {source.path for source in catalog_sources()}
        self.assertTrue(catalog_paths.isdisjoint(cv.EXCLUDED_LAUNDERER_PATHS))

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path))
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("dbc-mill-r193.py"))
        self.assertTrue(is_vendor_filename("dbc-loop-r193.py"))
        self.assertTrue(is_vendor_filename("dbc_leftover_lang_mill.py"))
        self.assertTrue(is_vendor_filename("dbc_r597_leftover3_mill.py"))
        self.assertTrue(is_excluded_launderer_path("experiments/dbc_r600_leftover3_cacheprod_mill.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/dbc-mill-r193.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "dbc"
        hits = []
        for name in ("catalog_ast.py", "catalog_extract.py", "catalog.py", "identity.py"):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_extractor_reads_literal_pairs(self):
        extracted = extract_mill_catalog(_LITERAL_SNIPPET, path="experiments/dbc-mill-r193.py")
        self.assertEqual(extracted["shape"], SHAPE_LITERAL)
        self.assertEqual(extracted["catalog_first"], 193)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "keep-a")
        self.assertEqual(extracted["pairs"][0]["success_plant"], "harbor-a")
        self.assertTrue(extracted["pairs"][0]["fail_handoff"])

    def test_extractor_reads_skip_extra_without_companion(self):
        extracted = extract_mill_catalog(_SKIP_EXTRA_SNIPPET, path="experiments/dbc-mill-r248.py")
        self.assertEqual(extracted["shape"], SHAPE_SKIP_EXTRA)
        self.assertEqual(extracted["n_extra"], 1)
        self.assertEqual(extracted["skip_slugs"], ["drop-me", "drop-me-left"])
        self.assertEqual(extracted["first_slug"], "extra-a")

    def test_extractor_composes_skip_extra_from_companion(self):
        companion = extract_mill_catalog(_LITERAL_SNIPPET, path="experiments/dbc-mill-r233.py")
        extra = extract_mill_catalog(_SKIP_EXTRA_SNIPPET, path="experiments/dbc-mill-r248.py")
        companion["mill_id"] = cv.R248_COMPANION_ID
        extra["mill_id"] = cv.R248_MILL_ID
        composed = compose_family_records(
            {cv.R248_COMPANION_ID: companion, cv.R248_MILL_ID: extra}
        )[cv.R248_MILL_ID]
        self.assertEqual(composed["n_rows"], 3)
        slugs = [row["success_slug"] for row in composed["pairs"]]
        self.assertEqual(slugs, ["keep-a", "keep-b", "extra-a"])

    def test_extractor_reads_suc_left_kwargs(self):
        extracted = extract_mill_catalog(_CTOR_SNIPPET, path="experiments/dbc-mill-r288.py")
        self.assertEqual(extracted["shape"], SHAPE_CTOR)
        self.assertEqual(extracted["first_slug"], "buf-mod-cache")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "softlockup-leftover")

    def test_extractor_reads_zip_tables(self):
        extracted = extract_mill_catalog(_ZIP_SNIPPET, path="experiments/dbc-mill-r933.py")
        self.assertEqual(extracted["shape"], SHAPE_ZIP_TABLES)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "botan-cache")
        self.assertEqual(extracted["last_slug"], "wolfssl-cache")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "gpio-amd-leftover")

    def test_extractor_reads_leftover_lang_zip(self):
        extracted = extract_mill_catalog(
            _LEFTOVER_LANG_SNIPPET, path="experiments/dbc_leftover_lang_mill.py"
        )
        self.assertEqual(extracted["shape"], SHAPE_LEFTOVER_LANG)
        self.assertEqual(extracted["pairs"][0]["success_plant"], "racket")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "zonefs-cnv-leftover")

    def test_extractor_reads_plant_build_aliases(self):
        extracted = extract_mill_catalog(_PLANT_SNIPPET, path="experiments/dbc-mill-r502-plants.py")
        self.assertEqual(extracted["shape"], SHAPE_PLANT_BUILD)
        self.assertEqual(extracted["first_slug"], "namd-charm-cache")
        self.assertEqual(extracted["pairs"][0]["fail_plant"], "harbor-fatutf")

    def test_loop_mill_path_constant(self):
        source = (
            "ROOT = Path(__file__).resolve().parents[1]\n"
            'DBC_MILL = ROOT / "experiments" / "dbc-mill-r193.py"\n'
        )
        self.assertEqual(extract_companion_path(source), "experiments/dbc-mill-r193.py")

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 32)
        self.assertEqual(CATALOG.n_pair_rows, 1252)
        self.assertEqual(CATALOG.slice, "r193")
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        r193 = CATALOG.mills["dbc-mill-r193"]
        self.assertEqual(r193.n_rows, 40)
        self.assertEqual(r193.catalog_first, 193)
        self.assertEqual(r193.first_slug, "texlive-fmt-cache")
        self.assertEqual(r193.last_slug, "flux-artifact-cache")
        self.assertEqual(len(r193.pairs), 40)
        self.assertEqual(r193.pairs[0]["success_plant"], "harbor-texlive")
        self.assertTrue(r193.pairs[0]["fail_handoff"])
        self.assertEqual(CATALOG.mills["dbc-mill-r248"].n_rows, 20)
        self.assertEqual(CATALOG.mills["dbc-mill-r248"].n_extra, 6)
        self.assertEqual(CATALOG.mills["dbc-mill-r647"].n_rows, 48)
        self.assertEqual(CATALOG.mills["dbc-mill-r647"].n_new, 36)
        self.assertEqual(CATALOG.mills["dbc-mill-r647"].n_inherited, 12)
        self.assertEqual(CATALOG.mills["dbc-mill-r1504"].n_rows, 48)
        self.assertEqual(len(CATALOG.mills["dbc-mill-r1504"].pairs), 48)
        self.assertEqual(CATALOG.n_deferred_pair_rows, cv.DEFERRED_PAIR_ROWS)
        self.assertEqual(sum(len(mill.pairs) for mill in CATALOG.mills.values()), cv.N_PAIR_ROWS)
        self.assertNotIn("dbc_r597_leftover3_mill", CATALOG.mills)
        self.assertNotIn("dbc_r600_leftover3_cacheprod_mill", CATALOG.mills)

    def test_pairs_jsonl_is_1212_deferred_of_1252(self):
        rows = load_pairs_jsonl()
        self.assertEqual(len(rows), 1212)
        self.assertEqual(len(rows), cv.DEFERRED_PAIR_ROWS)
        self.assertEqual(cv.SLICE_PAIR_ROWS + cv.DEFERRED_PAIR_ROWS, cv.N_PAIR_ROWS)
        mill_ids = {row["mill_id"] for row in rows}
        self.assertNotIn(cv.SLICE_MILL_ID, mill_ids)
        self.assertEqual(len(mill_ids), 31)
        self.assertNotIn("dbc_r597_leftover3_mill", mill_ids)
        self.assertNotIn("dbc_r600_leftover3_cacheprod_mill", mill_ids)
        paths = {row["source_path"] for row in rows}
        self.assertTrue(paths.isdisjoint(cv.EXCLUDED_LAUNDERER_PATHS))
        r1504 = [row for row in rows if row["mill_id"] == "dbc-mill-r1504"]
        self.assertEqual(len(r1504), 48)
        self.assertEqual(r1504[0]["success_slug"], CATALOG.mills["dbc-mill-r1504"].first_slug)
        self.assertEqual(r1504[-1]["success_slug"], CATALOG.mills["dbc-mill-r1504"].last_slug)

    def test_pairs_jsonl_stays_compact(self):
        text = pairs_jsonl_path().read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), cv.DEFERRED_PAIR_ROWS)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        self.assertEqual(sha256_bytes(text.encode("utf-8")), cv.PAIRS_SHA256)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            row = json.loads(line)
            self.assertEqual(set(row), set(cv.PAIR_JSONL_KEYS))

    def test_catalog_json_still_omits_deferred_bodies(self):
        document = json.loads(catalog_json_path().read_text(encoding="utf-8"))
        for mill_id, row in document["mills"].items():
            if mill_id == cv.SLICE_MILL_ID:
                self.assertEqual(len(row.get("pairs") or ()), cv.SLICE_PAIR_ROWS)
            else:
                self.assertFalse(row.get("pairs"))

    def test_git_ls_files_has_no_mill_or_loop_scripts(self):
        tracked = subprocess.check_output(["git", "ls-files"], cwd=REPO, text=True)
        names = [Path(path).name for path in tracked.splitlines()]
        forbidden = [name for name in names if is_vendor_filename(name)]
        self.assertEqual(forbidden, [])


class DbcLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        records = {}
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
            records[source.mill_id] = live
        composed = compose_family_records(records)
        mills = []
        for source in catalog_sources():
            live = composed[source.mill_id]
            committed = CATALOG.mills[source.mill_id]
            self.assertEqual(live["n_rows"], committed.n_rows, source.mill_id)
            self.assertEqual(live["first_slug"], committed.first_slug, source.mill_id)
            self.assertEqual(live["last_slug"], committed.last_slug, source.mill_id)
            self.assertEqual(live["catalog_first"], committed.catalog_first, source.mill_id)
            self.assertEqual(live["sha256"], committed.sha256, source.mill_id)
            self.assertEqual(live["shape"], committed.shape, source.mill_id)
            mills.append(mill_summary(live, include_pairs=source.mill_id == cv.SLICE_MILL_ID))
        self.assertEqual(
            dumps_catalog(catalog_document(mills)),
            catalog_json_path().read_text(encoding="utf-8"),
        )
        self.assertEqual(
            dumps_pairs_jsonl(deferred_pair_rows(composed, catalog_sources())),
            pairs_jsonl_path().read_text(encoding="utf-8"),
        )

    def test_loop_and_hop_scripts_name_companion_mills(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        for source in (*loop_sources(), *hop_sources()):
            if source.companion_mill_path is None:
                continue
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
            self.assertEqual(list(dest.glob("dbc-mill*.py")), [])


if __name__ == "__main__":
    unittest.main()
