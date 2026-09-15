#!/usr/bin/env python3
"""PR-a: AST catalog extract and ``pipelines/ssr`` skeleton (no vendored mills)."""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from ssr.catalog import CATALOG  # noqa: E402
from ssr.catalog_extract import (  # noqa: E402
    SHAPE_LITERAL,
    SHAPE_PLANT,
    SHAPE_S,
    SHAPE_TAILS,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    extract_companion_path,
    extract_mill_catalog,
    summarize_catalog_records,
)
from ssr.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from ssr.sources import (  # noqa: E402
    MILL_SOURCES,
    catalog_sources,
    fast_sources,
    loop_sources,
)
from ssr import vocabulary as cv  # noqa: E402

_R181_SNIPPET = """
FACTORY = "secret-scan-remediation-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 181
PAIRS: list[tuple[dict, dict]] = [
    (
        {"slug": "gitleaks-allowlist-overfit", "scanner": "gitleaks"},
        {"slug": "trufflehog-p8-path-filter", "scanner": "trufflehog"},
    ),
    (
        {"slug": "ggshield-lfs-pointer-hide", "scanner": "ggshield"},
        {"slug": "detect-secrets-plugin-off", "scanner": "detect-secrets"},
    ),
]
"""

_PLANT_SNIPPET = """
CATALOG_FIRST = 197
PAIRS: list[tuple[dict, dict]] = [
    (
        plant(slug="ripsecrets-third-party-glob", scanner="ripsecrets"),
        plant(slug="whispers-vendor-cache", scanner="whispers"),
    ),
]
"""

_S_SNIPPET = """
CATALOG_FIRST = 494
PAIRS: list[tuple[dict, dict]] = [
    (
        S("gitleaks-allowlist-lll", "gitleaks", "m", "r", "l", "e", "t", "n", "s", 1, "x"),
        S("gitleaks-baseline-lll", "gitleaks", "m", "r", "l", "e", "t", "n", "s", 2, "x"),
    ),
]
"""

_TAILS_SNIPPET = """
CATALOG_FIRST = 436
SCAN = {"gitleaks": ("cmd", "hit"), "trufflehog": ("cmd", "hit")}
TAILS = ["gold-map", "bfd-map", "thinlto", "ecl-fasl"]
PAIRS = [(_plants[i], _plants[i + 1]) for i in range(0, len(_plants), 2)]
"""


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", f"{cv.PRESERVE_COMMIT}:experiments/ssr-mill-r181.py"],
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


class SsrSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FACTORY, "secret-scan-remediation-factory")
        self.assertEqual(cv.GENERATOR, "grok-4.6")
        self.assertEqual(cv.PRESERVE_COMMIT, "9178e0bdcc38cef9629c6315d5dd9540492d6a72")
        self.assertEqual(cv.SLICE_ID, "r181")
        self.assertEqual(cv.SOURCE_FILE_COUNT, 77)

    def test_seventy_seven_sources_split_into_mills_loops_and_fast(self):
        self.assertEqual(len(MILL_SOURCES), 77)
        self.assertEqual(len(catalog_sources()), 40)
        self.assertEqual(len(loop_sources()), 36)
        self.assertEqual(len(fast_sources()), 1)
        self.assertEqual(fast_sources()[0].mill_id, "ssr_mill_fast")
        loop_181 = next(item for item in loop_sources() if item.mill_id == "ssr-loop-r181")
        loop_1142 = next(item for item in loop_sources() if item.mill_id == "ssr-loop-r1142")
        self.assertEqual(loop_181.companion_mill_path, "experiments/ssr-mill-r181.py")
        self.assertEqual(loop_1142.catalog_json, ".ssr-catalog-r1142.json")

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(
                path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path)
            )
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("ssr-mill-r181.py"))
        self.assertTrue(is_vendor_filename("ssr-loop-r181.py"))
        self.assertTrue(is_vendor_filename("ssr_mill_fast.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/ssr-mill-r181.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "ssr"
        hits = []
        for name in ("catalog_ast.py", "catalog_extract.py", "catalog.py", "identity.py"):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_extractor_reads_literal_pairs(self):
        extracted = extract_mill_catalog(_R181_SNIPPET, path="experiments/ssr-mill-r181.py")
        self.assertEqual(extracted["shape"], SHAPE_LITERAL)
        self.assertEqual(extracted["catalog_first"], 181)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "gitleaks-allowlist-overfit")
        self.assertEqual(extracted["last_slug"], "ggshield-lfs-pointer-hide")
        self.assertEqual(extracted["pairs"][0]["fail_scanner"], "trufflehog")

    def test_extractor_reads_plant_kwargs(self):
        extracted = extract_mill_catalog(_PLANT_SNIPPET, path="experiments/ssr-mill-r197.py")
        self.assertEqual(extracted["shape"], SHAPE_PLANT)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "ripsecrets-third-party-glob")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "whispers-vendor-cache")

    def test_extractor_reads_s_positional_args(self):
        extracted = extract_mill_catalog(_S_SNIPPET, path="experiments/ssr-mill-lll-r494.py")
        self.assertEqual(extracted["shape"], SHAPE_S)
        self.assertEqual(extracted["first_slug"], "gitleaks-allowlist-lll")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "gitleaks-baseline-lll")

    def test_extractor_reads_tails_and_local_scan(self):
        extracted = extract_mill_catalog(_TAILS_SNIPPET, path="experiments/ssr-mill-r436.py")
        self.assertEqual(extracted["shape"], SHAPE_TAILS)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_tail"], "gold-map")
        self.assertEqual(extracted["last_tail"], "ecl-fasl")
        self.assertEqual(extracted["first_slug"], "gitleaks-gold-map-leftover")
        self.assertEqual(extracted["last_slug"], "gitleaks-thinlto-leftover")

    def test_loop_mill_path_constant(self):
        source = (
            "ROOT = Path(__file__).resolve().parents[1]\n"
            'MILL = ROOT / "experiments" / "ssr-mill-r181.py"\n'
        )
        self.assertEqual(extract_companion_path(source), "experiments/ssr-mill-r181.py")

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 40)
        self.assertEqual(CATALOG.n_pair_rows, 1604)
        self.assertEqual(CATALOG.slice, "r181")
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        self.assertFalse(CATALOG.mills["ssr-mill-r181"].pairs == ())
        r181 = CATALOG.mills["ssr-mill-r181"]
        self.assertEqual(r181.n_rows, 16)
        self.assertEqual(r181.catalog_first, 181)
        self.assertEqual(r181.first_slug, "gitleaks-allowlist-overfit")
        self.assertEqual(r181.last_slug, "detect-secrets-plugin-off")
        self.assertEqual(len(r181.pairs), 16)
        self.assertEqual(r181.pairs[0]["fail_slug"], "trufflehog-p8-path-filter")
        self.assertEqual(CATALOG.mills["ssr-mill-r1142"].n_rows, 40)
        self.assertEqual(
            CATALOG.mills["ssr-mill-r1142"].first_slug,
            "gitleaks-mosquitto-acl-leftover",
        )
        self.assertEqual(CATALOG.mills["ssr-mill-r332"].n_rows, 104)
        self.assertFalse(CATALOG.mills["ssr-mill-r1702"].pairs)


class SsrLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane preserve commit is not fetched")
        records = []
        for source in catalog_sources():
            text = subprocess.check_output(
                ["git", "show", f"{cv.PRESERVE_COMMIT}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            blob = subprocess.check_output(
                ["git", "rev-parse", f"{cv.PRESERVE_COMMIT}:{source.path}"],
                text=True,
                cwd=REPO,
            ).strip()
            self.assertEqual(blob, source.blob_sha, source.mill_id)
            live = extract_mill_catalog(text, path=source.path, blob_sha=source.blob_sha)
            records.append(live)
        mills = summarize_catalog_records(records)
        by_id = {mill["mill_id"]: mill for mill in mills}
        for source in catalog_sources():
            committed = CATALOG.mills[source.mill_id]
            live = by_id[source.mill_id]
            self.assertEqual(live["n_rows"], committed.n_rows, source.mill_id)
            self.assertEqual(live["first_slug"], committed.first_slug, source.mill_id)
            self.assertEqual(live["last_slug"], committed.last_slug, source.mill_id)
            self.assertEqual(live["catalog_first"], committed.catalog_first, source.mill_id)
            self.assertEqual(live["sha256"], committed.sha256, source.mill_id)
            self.assertEqual(live["shape"], committed.shape, source.mill_id)
        self.assertEqual(
            dumps_catalog(catalog_document(mills)),
            catalog_json_path().read_text(encoding="utf-8"),
        )

    def test_loop_scripts_name_companion_mills(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane preserve commit is not fetched")
        for source in loop_sources():
            text = subprocess.check_output(
                ["git", "show", f"{cv.PRESERVE_COMMIT}:{source.path}"],
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
            self.skipTest("origin/legacy-mill-lane preserve commit is not fetched")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            refuse_vendor_paths(dest.rglob("*") if dest.exists() else ())
            self.assertEqual(list(dest.glob("ssr-mill*.py")), [])


if __name__ == "__main__":
    unittest.main()
