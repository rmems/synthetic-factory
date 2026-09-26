#!/usr/bin/env python3
"""FAMILY=sir: AST catalog extract of leftover mills (no vendored publishers)."""

from __future__ import annotations

import ast
import json
import subprocess  # nosec B404 -- fixed /usr/bin/git argv reads pinned preserve-commit blobs only
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from search.sources import HOME_MILL_SOURCES, R31_SOURCE  # noqa: E402
from sir.catalog import CATALOG, _pair_record, load_catalog  # noqa: E402
from sir.catalog_ast import UNSET, literal_value  # noqa: E402
from sir.catalog_extract import (  # noqa: E402
    SHAPE_PAIR_6TUPLES,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    dumps_pairs,
    extract_mill_catalog,
    mill_summary,
    pairs_jsonl_path,
    write_catalog_files,
)
import sir.catalog_extract as catalog_extract_mod  # noqa: E402
from sir.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from sir.sources import MILL_SOURCES, catalog_sources  # noqa: E402
from sir import vocabulary as cv  # noqa: E402

_LEFTOVER_SNIPPET = """
'''search-index-rebuild mill leftover leftover leftover r72+.'''
FACTORY = "search-index-rebuild-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 72
PAIRS = [
    (
        (
            "meili-swap-leftover3-rebuild",
            "Meilisearch leftover3 swap",
            "drop index",
            "create index + swapIndexes leftover3",
            "swapIndexes leftover3; do not drop the live Meilisearch index.",
            "https://www.meilisearch.com/docs/reference/api/swap_indexes",
        ),
        (
            "meili-drop-index-leftover3-handoff",
            "Meilisearch leftover3 drop",
            "drop index",
            "nightly drop index leftover3",
            "Ticket is swapIndexes leftover3.",
            "https://www.meilisearch.com/docs/reference/api/indexes",
        ),
    ),
]
"""

_CHAIN_SNIPPET = """
from importlib.machinery import SourceFileLoader
from pathlib import Path
HERE = Path(__file__).resolve().parent
_base = SourceFileLoader("sir31", str(HERE / "sir-mill-r31.py")).load_module()
CATALOG_FIRST = 52
PAIRS = [
    (
        ("pinecone-ns-rebuild", "Pinecone namespace", "delete index",
         "create namespace + upsert swap", "Rebuild a Pinecone namespace.",
         "https://docs.pinecone.io/guides/indexes/understanding-indexes"),
        ("vespa-hnsw-handoff", "Vespa", "delete index", "nightly delete",
         "Ticket is namespace swap.", "https://docs.vespa.ai/"),
    ),
]
"""

_PUBLISHER_NAMES = frozenset(
    {
        "build_success",
        "build_partial",
        "candidates",
        "try_reserve",
        "run_one",
        "main",
    }
)


def _legacy_available() -> bool:
    reference = f"{cv.PRESERVE_COMMIT}:{catalog_sources()[0].path}"
    result = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603 -- fixed git argv, no shell
        ["/usr/bin/git", "show", reference],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _git_text(command: str, reference: str) -> str:
    return subprocess.check_output(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603 -- fixed git argv, no shell
        ["/usr/bin/git", command, reference],
        text=True,
        cwd=REPO,
    )


def _module_uses_exec(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        callee = getattr(node, "func", None)
        if isinstance(callee, ast.Name) and callee.id in {"exec", "eval"}:
            hits.append(f"{path.name}:{node.lineno}:{callee.id}")
    return hits


def _package_function_names() -> set[str]:
    names: set[str] = set()
    for path in (REPO / "pipelines" / "sir").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
    return names


class SirSkeletonTests(unittest.TestCase):
    def test_literal_containers_resolve_all_members_or_remain_unknown(self):
        env = {"name": "resolved"}
        expression = "{'key': [name, (1, 2)], 'set': {3, 4}}"
        parsed = ast.parse(expression, mode="eval").body
        self.assertEqual(literal_value(parsed, env), {"key": ["resolved", (1, 2)], "set": {3, 4}})
        for expression in ("{missing: name}", "{'key': missing}", "[name, missing]", "{**unknown}"):
            with self.subTest(expression=expression):
                self.assertIs(literal_value(ast.parse(expression, mode="eval").body, env), UNSET)

    def test_catalog_does_not_duplicate_search_home_ownership(self):
        home_ids = {source.mill_id for source in HOME_MILL_SOURCES}
        self.assertTrue(home_ids.isdisjoint(CATALOG.mills))
        self.assertTrue(home_ids.isdisjoint(source.mill_id for source in MILL_SOURCES))
        self.assertEqual(catalog_sources()[0].loads_sibling, R31_SOURCE.path)

    def test_home_extraction_requires_canonical_search_package(self):
        with self.assertRaisesRegex(ValueError, "search"):
            extract_mill_catalog(_CHAIN_SNIPPET, path="experiments/sir-mill-r52.py")

    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FAMILY, "sir")
        self.assertEqual(cv.FAMILY_PREFIX, "sir")
        self.assertEqual(cv.FACTORY, "search-index-rebuild-factory")
        self.assertEqual(cv.GENERATOR, "grok-4.6")
        self.assertEqual(cv.PRESERVE_COMMIT, "854c59b31eb9bde983f79c8a1adf3b40d04100a9")
        self.assertEqual(cv.SLICE_ID, "leftover-mills")

    def test_two_leftover_catalog_mill_sources(self):
        self.assertEqual(len(MILL_SOURCES), 2)
        self.assertEqual(len(catalog_sources()), 2)
        self.assertEqual(
            [source.mill_id for source in catalog_sources()],
            [
                "sir-mill-leftover3-r72",
                "sir_r108_leftover3d_mill",
            ],
        )
        self.assertEqual(catalog_sources()[0].catalog_first, 72)
        self.assertEqual(catalog_sources()[0].kind, cv.KIND_LEFTOVER_PAIRS)
        self.assertEqual(catalog_sources()[1].n_hops, 11)
        self.assertEqual(catalog_sources()[0].loads_sibling, R31_SOURCE.path)

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path))
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("sir-mill-r31.py"))
        self.assertTrue(is_vendor_filename("sir-mill-leftover3-r72.py"))
        self.assertTrue(is_vendor_filename("sir-loop-leftover3-r72.py"))
        self.assertTrue(is_vendor_filename("sir_r108_leftover3d_mill.py"))
        self.assertTrue(is_vendor_filename("search_index_rebuild_leftover3_mill.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/sir-mill-leftover3-r72.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "sir"
        hits = [hit for module in sorted(package.glob("*.py")) for hit in _module_uses_exec(module)]
        self.assertEqual(hits, [])

    def test_package_has_no_launderer_publishers(self):
        names = _package_function_names()
        self.assertEqual(names & _PUBLISHER_NAMES, set())
        self.assertFalse((REPO / "pipelines" / "sir" / "generate.py").exists())
        self.assertFalse((REPO / "pipelines" / "sir" / "cli.py").exists())

    def test_extractor_reads_literal_pairs_without_hops(self):
        extracted = extract_mill_catalog(
            _LEFTOVER_SNIPPET,
            path="experiments/sir-mill-leftover3-r72.py",
        )
        self.assertEqual(extracted["shape"], SHAPE_PAIR_6TUPLES)
        self.assertEqual(extracted["kind"], cv.KIND_LEFTOVER_PAIRS)
        self.assertEqual(extracted["catalog_first"], 72)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["n_hops"], 0)
        self.assertEqual(extracted["first_slug"], "meili-swap-leftover3-rebuild")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "meili-drop-index-leftover3-handoff")
        self.assertTrue(extracted["pairs"][0]["fail_handoff"])
        self.assertEqual(extracted["hops"], [])
        self.assertEqual(extracted["loads_sibling"], "")
        self.assertEqual(
            extracted["doc_first_line"],
            "search-index-rebuild mill leftover leftover leftover r72+.",
        )

    def test_unpinned_loader_source_is_refused_without_loading(self):
        # Sibling syntax is projected only from exact pinned archive source.
        with self.assertRaises(ValueError):
            extract_mill_catalog(_CHAIN_SNIPPET, path="experiments/sir-mill-leftover3-r72.py")

    def test_extractor_refuses_non_literal_pairs(self):
        source = (
            'FACTORY = "search-index-rebuild-factory"\n'
            'GEN = "grok-4.6"\n'
            "CATALOG_FIRST = 72\n"
            "PAIRS = [leftover_pair()]\n"
        )
        with self.assertRaises(ValueError):
            extract_mill_catalog(source, path="experiments/sir-mill-leftover3-r72.py")

    def test_extractor_refuses_nonliteral_reassignment(self):
        for assignment in ("PAIRS = rebuild()", "PAIRS = alias = rebuild()"):
            with self.subTest(assignment=assignment), self.assertRaises(ValueError):
                extract_mill_catalog(
                    _LEFTOVER_SNIPPET + f"\n{assignment}\n",
                    path="experiments/sir-mill-leftover3-r72.py",
                )

    def test_extractor_preserves_value_after_annotation_without_assignment(self):
        extracted = extract_mill_catalog(
            _LEFTOVER_SNIPPET + "\nPAIRS: list\n",
            path="experiments/sir-mill-leftover3-r72.py",
        )
        self.assertEqual(extracted["first_slug"], "meili-swap-leftover3-rebuild")

    def test_extractor_refuses_explicit_nonliteral_optional_bindings(self):
        for field in ("FACTORY", "GEN", "N_ROUNDS", "HOP"):
            for assignment in (f"{field} = compute()", f"{field} = alias = compute()"):
                with self.subTest(assignment=assignment), self.assertRaises(ValueError):
                    extract_mill_catalog(
                        _LEFTOVER_SNIPPET + f"\n{assignment}\n",
                        path="experiments/sir-mill-leftover3-r72.py",
                    )

    def test_loader_refuses_embedded_mill_identity_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "pairs.jsonl").write_bytes(pairs_jsonl_path().read_bytes())
            header = json.loads(catalog_json_path().read_text(encoding="utf-8"))
            header["mills"]["sir-mill-leftover3-r72"]["mill_id"] = "sir_r108_leftover3d_mill"
            (directory / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mill_id"):
                load_catalog(directory / "CATALOG.json")

    def test_loader_refuses_fabricated_source_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "pairs.jsonl").write_bytes(pairs_jsonl_path().read_bytes())
            header = json.loads(catalog_json_path().read_text(encoding="utf-8"))
            header["source_ref"] = "other-repository/main"
            (directory / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source_ref"):
                load_catalog(directory / "CATALOG.json")

    def test_loader_refuses_invalid_middle_pair_values(self):
        invalid = (
            ("success_slug", None),
            ("fail_url", 12),
            ("success_ticket", ""),
            ("fail_handoff", False),
            ("fail_handoff", 1),
        )
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "CATALOG.json").write_bytes(catalog_json_path().read_bytes())
            for field, value in invalid:
                with self.subTest(field=field, value=value):
                    lines = pairs_jsonl_path().read_text(encoding="utf-8").split("\n")
                    row = json.loads(lines[1])
                    row[field] = value
                    lines[1] = json.dumps(row, separators=(",", ":"))
                    (directory / "pairs.jsonl").write_text("\n".join(lines), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_catalog(directory / "CATALOG.json")

    def test_loader_refuses_non_lf_pair_framing(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "CATALOG.json").write_bytes(catalog_json_path().read_bytes())
            for separator in (b"\r\n", b"\x0b", b"\x1e", b"\xc2\x85"):
                with self.subTest(separator=separator):
                    pairs = pairs_jsonl_path().read_bytes().replace(b"\n", separator, 1)
                    (directory / "pairs.jsonl").write_bytes(pairs)
                    with self.assertRaises(ValueError):
                        load_catalog(directory / "CATALOG.json")

    def test_pair_parser_preserves_unicode_separators_inside_json_strings(self):
        row = json.loads(pairs_jsonl_path().read_text(encoding="utf-8").split("\n")[0])
        ticket = "Keep \u0085, \u2028, and \u2029 within the ticket."
        row["success_ticket"] = ticket
        line = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        self.assertEqual(_pair_record(line, "unicode pair")["success_ticket"], ticket)

    def test_loader_refuses_unknown_pair_mill(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            header = catalog_json_path().read_text(encoding="utf-8")
            pairs = pairs_jsonl_path().read_text(encoding="utf-8")
            row = json.loads(pairs.splitlines()[0])
            row["mill_id"] = "unknown-mill"
            (directory / "CATALOG.json").write_text(header, encoding="utf-8")
            (directory / "pairs.jsonl").write_text(pairs + json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mill IDs"):
                load_catalog(directory / "CATALOG.json")

    def test_loader_refuses_drifted_mill_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "pairs.jsonl").write_bytes(pairs_jsonl_path().read_bytes())
            for field in ("factory", "generator", "shape"):
                with self.subTest(field=field):
                    header = json.loads(catalog_json_path().read_text(encoding="utf-8"))
                    header["mills"]["sir-mill-leftover3-r72"][field] = "other"
                    (directory / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "vocabulary"):
                        load_catalog(directory / "CATALOG.json")

    def test_extractor_refuses_empty_pairs(self):
        source = "FACTORY = 'search-index-rebuild-factory'\nGEN = 'grok-4.6'\nCATALOG_FIRST = 72\nPAIRS = []\n"
        with self.assertRaises(ValueError):
            extract_mill_catalog(source, path="experiments/sir-mill-leftover3-r72.py")

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 2)
        self.assertEqual(CATALOG.n_pair_rows, 32)
        self.assertEqual(CATALOG.slice, "leftover-mills")
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        leftover3 = CATALOG.mills["sir-mill-leftover3-r72"]
        leftover3d = CATALOG.mills["sir_r108_leftover3d_mill"]
        self.assertEqual(leftover3.n_rows, 16)
        self.assertEqual(leftover3.first_slug, "meili-swap-leftover3-rebuild")
        self.assertEqual(leftover3.last_slug, "paradedb-bm25-leftover3-rebuild")
        self.assertEqual(leftover3.loads_sibling, "experiments/sir-mill-r31.py")
        self.assertEqual(leftover3d.n_rows, 16)
        self.assertEqual(leftover3d.catalog_first, 108)
        self.assertEqual(leftover3d.first_slug, "xapian-flint-leftover3d-rebuild")
        self.assertEqual(leftover3d.last_slug, "haystack-pipeline-leftover3d-rebuild")
        self.assertEqual(leftover3d.n_hops, 11)
        self.assertIn("email-webhook-retry-factory", leftover3d.hops)

    def test_pairs_jsonl_stays_compact(self):
        text = pairs_jsonl_path().read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), 32)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            row = json.loads(line)
            self.assertEqual(set(row), set(cv.PAIR_FIELD_ORDER))

    def test_header_omits_pair_bodies(self):
        document = json.loads(catalog_json_path().read_text(encoding="utf-8"))
        for mill in document["mills"].values():
            self.assertNotIn("pairs", mill)
        self.assertEqual(document["n_pair_rows"], 32)
        self.assertIn("never imported or executed", document["extraction"])

    def test_write_catalog_files_leaves_existing_artifacts_when_pairs_staging_fails(self):
        mill = extract_mill_catalog(
            _LEFTOVER_SNIPPET,
            path="experiments/sir-mill-leftover3-r72.py",
        )
        mills = [mill]
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            catalog_path = catalog_json_path(package_dir)
            pairs_path = pairs_jsonl_path(package_dir)
            original_catalog = '{"catalog": "unchanged"}\n'
            original_pairs = '{"pair": "unchanged"}\n'
            catalog_path.write_text(original_catalog, encoding="utf-8")
            pairs_path.write_text(original_pairs, encoding="utf-8")
            real_write = catalog_extract_mod.write_exclusive_text
            calls = 0

            def staging_write(path, content, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated pairs.jsonl staging failure")
                return real_write(path, content, **kwargs)

            with patch.object(
                catalog_extract_mod, "write_exclusive_text", side_effect=staging_write
            ):
                with self.assertRaises(OSError):
                    write_catalog_files(mills, package_dir=package_dir)
            self.assertEqual(catalog_path.read_text(encoding="utf-8"), original_catalog)
            self.assertEqual(pairs_path.read_text(encoding="utf-8"), original_pairs)
            self.assertEqual(list(package_dir.glob(".*.migrating")), [])

    def test_hops_are_catalogued_not_executed(self):
        self.assertIn("email-webhook-retry-factory", CATALOG.hops)
        self.assertNotIn(cv.FACTORY, CATALOG.hops)
        tree = ast.parse(
            (REPO / "pipelines" / "sir" / "catalog_extract.py").read_text(encoding="utf-8")
        )
        assigned = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        self.assertNotIn("candidates", assigned)
        self.assertNotIn("try_reserve", assigned)
        self.assertNotIn("run_one", assigned)


class SirLegacyExtractTests(unittest.TestCase):
    def test_changed_archive_bytes_lose_text_projection_exception(self):
        if not _legacy_available():
            self.skipTest("sir preserve commit is not available")
        for source in catalog_sources():
            text = _git_text("show", f"{cv.PRESERVE_COMMIT}:{source.path}")
            for appendix in ('\nunknown_effect()\n', '\n# changed source\n'):
                with self.subTest(path=source.path, appendix=appendix), self.assertRaises(ValueError):
                    extract_mill_catalog(text + appendix, path=source.path,
                                         blob_sha=source.blob_sha)

    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("sir preserve commit is not available")
        mills = []
        for source in catalog_sources():
            reference = f"{cv.PRESERVE_COMMIT}:{source.path}"
            text = _git_text("show", reference)
            blob = _git_text("rev-parse", reference).strip()
            self.assertEqual(blob, source.blob_sha, source.mill_id)
            live = extract_mill_catalog(text, path=source.path, blob_sha=source.blob_sha)
            committed = CATALOG.mills[source.mill_id]
            fields = (
                "n_rows",
                "first_slug",
                "last_slug",
                "catalog_first",
                "sha256",
                "shape",
                "loads_sibling",
            )
            for field in fields:
                self.assertEqual(
                    live[field], getattr(committed, field), f"{source.mill_id} {field}"
                )
            self.assertEqual(live["hops"], list(committed.hops), source.mill_id)
            mills.append(live)
        self.assertEqual(
            dumps_catalog(catalog_document(mills)),
            catalog_json_path().read_text(encoding="utf-8"),
        )
        self.assertEqual(dumps_pairs(mills), pairs_jsonl_path().read_text(encoding="utf-8"))
        summaries = [mill_summary(mill) for mill in mills]
        self.assertEqual(len(summaries), 2)

    def test_git_show_is_the_only_legacy_read(self):
        if not _legacy_available():
            self.skipTest("sir preserve commit is not available")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            refuse_vendor_paths(dest.rglob("*") if dest.exists() else ())
            self.assertEqual(list(dest.glob("sir-mill*.py")), [])
            self.assertEqual(list(dest.glob("sir-loop*.py")), [])


if __name__ == "__main__":
    unittest.main()
