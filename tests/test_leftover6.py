#!/usr/bin/env python3
"""FAMILY=leftover6: AST catalog extract of leftover6 mills (no vendored publishers)."""

from __future__ import annotations

import ast
import json
import shutil
import subprocess  # nosec B404 -- fixed git argv for pinned legacy-mill-lane blobs only.
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
from tests.pipeline_import_test_support import clean_package_imports, direct_pipeline_path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "pipelines" / "leftover6"
CONFIG_DIR = ROOT / "config" / "leftover6"
CATALOG_JSON = CONFIG_DIR / "CATALOG.json"
PAIRS_JSONL = CONFIG_DIR / "pairs.jsonl"
PLANTS_JSONL = CONFIG_DIR / "plants.jsonl"
GIT = Path(shutil.which("git") or "/usr/bin/git").resolve()

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
    if not GIT.is_file():
        return False
    try:
        for commit in {mill.preserve_commit for mill in CATALOG.catalogs}:
            subprocess.check_output(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603 -- fixed git argv, no shell
                [str(GIT), "cat-file", "-e", f"{commit}^{{commit}}"],
                cwd=ROOT,
                stderr=subprocess.DEVNULL,
            )
        return True
    except subprocess.CalledProcessError:
        return False


def _git_show(commit: str, path: str) -> str:
    return subprocess.check_output(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603 -- fixed git argv, no shell
        [str(GIT), "show", f"{commit}:{path}"], text=True, cwd=ROOT
    )


def _git_blob(commit: str, path: str) -> str:
    return subprocess.check_output(  # nosec B603 -- fixed git argv, no shell
        [str(GIT), "rev-parse", f"{commit}:{path}"], text=True, cwd=ROOT
    ).strip()


def _catalog_rows() -> list[dict[str, object]]:
    return [json.loads(line) for line in PAIRS_JSONL.read_text(encoding="utf-8").splitlines()]


class _CatalogFixture:
    def __init__(self, *, header=None, pairs=None, plants=None):
        self.header = CATALOG_JSON.read_bytes() if header is None else header
        self.pairs = PAIRS_JSONL.read_bytes() if pairs is None else pairs
        self.plants = PLANTS_JSONL.read_bytes() if plants is None else plants
        self._temporary = tempfile.TemporaryDirectory()

    def __enter__(self) -> Path:
        directory = Path(self._temporary.__enter__())
        (directory / "CATALOG.json").write_bytes(_as_bytes(self.header))
        (directory / "pairs.jsonl").write_bytes(_as_bytes(self.pairs))
        (directory / "plants.jsonl").write_bytes(_as_bytes(self.plants))
        return directory

    def __exit__(self, *args) -> None:
        self._temporary.__exit__(*args)


def _as_bytes(value: str | bytes) -> bytes:
    return value.encode("utf-8") if isinstance(value, str) else value


def _fixture(**changes) -> _CatalogFixture:
    return _CatalogFixture(**changes)


def _extract_live_source(mill):
    text = _git_show(mill.preserve_commit, mill.source_path)
    blob = _git_blob(mill.preserve_commit, mill.source_path)
    live = extract_source(text, path=mill.source_path, blob_sha=blob)
    _assert_live_source_metadata(live, mill)
    return live


def _assert_live_source_metadata(live, mill) -> None:
    expected = {
        "path": mill.source_path,
        "kind": mill.kind,
        "blob_sha": mill.source_blob_sha1,
        "source_lines": mill.source_lines,
        "catalog_first": mill.catalog_first,
        "factory": mill.factory,
        "generator": CATALOG.generator,
        "n_rows": mill.n_rows,
        "first_slug": mill.first_slug,
        "last_slug": mill.last_slug,
        "sha256": mill.source_sha256,
        "shape": mill.shape,
    }
    for field, value in expected.items():
        if live[field] != value:
            raise AssertionError(f"{mill.source_path} {field} drifted")


def _append_live_rows(live, mill, pair_rows, plant_rows) -> None:
    rows = [{"source_path": mill.source_path, **row} for row in live["rows"]]
    if live["kind"] == "sbox-plants":
        plant_rows.extend(rows)
    else:
        pair_rows.extend(rows)


def _module_uses_exec(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id in {"exec", "eval"}:
            hits.append(f"{path.name}:{node.lineno}:{node.func.id}")
    return hits


class Leftover6CatalogTests(unittest.TestCase):
    def test_changed_archive_bytes_lose_text_projection_exception(self):
        if not _legacy_available():
            self.skipTest("leftover6 preserve commits are not available")
        for mill in CATALOG.catalogs:
            source = _git_show(mill.preserve_commit, mill.source_path)
            for appendix in ('\nunknown_effect()\n', '\n# changed source\n'):
                with self.subTest(path=mill.source_path, appendix=appendix), self.assertRaises(ValueError):
                    extract_source(source + appendix, path=mill.source_path,
                                   blob_sha=mill.source_blob_sha1)

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
        for path in PACKAGE.glob("*.py"):
            hits.extend(_module_uses_exec(path))
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
        with clean_package_imports(), direct_pipeline_path():
            import leftover6.catalog as direct
            import pipelines.leftover6.catalog as packaged
            import leftover6.catalog_ast as direct_ast
            import pipelines.leftover6.catalog_ast as packaged_ast
            import leftover6.catalog_literals as direct_literals
            import pipelines.leftover6.catalog_literals as packaged_literals
            self.assertIs(direct, packaged)
            self.assertIs(direct.CatalogError, packaged.CatalogError)
            self.assertIs(direct_ast, packaged_ast)
            self.assertIs(direct_ast.UNSET, packaged_ast.UNSET)
            self.assertIs(direct_literals, packaged_literals)
        with clean_package_imports(), direct_pipeline_path():
            import pipelines.leftover6.catalog as packaged_first
            import leftover6.catalog as direct_second
            import pipelines.leftover6.catalog_ast as packaged_ast_first
            import leftover6.catalog_ast as direct_ast_second
            import pipelines.leftover6.catalog_literals as packaged_literals_first
            import leftover6.catalog_literals as direct_literals_second
            self.assertIs(packaged_first, direct_second)
            self.assertIs(packaged_first.CatalogError, direct_second.CatalogError)
            self.assertIs(packaged_ast_first, direct_ast_second)
            self.assertIs(packaged_ast_first.UNSET, direct_ast_second.UNSET)
            self.assertIs(packaged_literals_first, direct_literals_second)

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
        rows = _catalog_rows()
        del rows[0]["ticket"]
        with _fixture(pairs=dumps_jsonl(rows)) as dest:
            with self.assertRaisesRegex(CatalogError, "keys differ"):
                load_catalog(dest)

    def test_loader_normalizes_non_scalar_unicode_to_catalog_error(self):
        rows = _catalog_rows()
        rows[0]['fail'] = '\ud800'
        payload = ''.join(json.dumps(row) + '\n' for row in rows)
        with _fixture(pairs=payload) as directory:
            with self.assertRaises(CatalogError):
                load_catalog(directory)

    def test_loader_refuses_a_wrong_pair_value_type(self):
        rows = _catalog_rows()
        rows[0]["round"] = "260"
        with _fixture(pairs=dumps_jsonl(rows)) as dest:
            with self.assertRaisesRegex(CatalogError, "round must be an integer"):
                load_catalog(dest)

    def test_loader_refuses_a_non_string_pair_kind(self):
        rows = _catalog_rows()
        rows[0]["kind"] = []
        with _fixture(pairs=dumps_jsonl(rows)) as dest:
            with self.assertRaisesRegex(CatalogError, "kind is not a leftover6 pair"):
                load_catalog(dest)

    def test_loader_refuses_duplicate_json_keys_and_non_lf_framing(self):
        pairs = PAIRS_JSONL.read_bytes()
        duplicate = pairs.replace(b'"kind":"gql-pairs"', b'"kind":"gql-pairs","kind":"gql-pairs"', 1)
        for label, candidate, expected in (
            ("duplicate", duplicate, "duplicate JSON object key"),
            ("crlf", pairs.replace(b"\n", b"\r\n"), "carriage returns"),
        ):
            with self.subTest(label=label), _fixture(pairs=candidate) as dest:
                with self.assertRaisesRegex(CatalogError, expected):
                    load_catalog(dest)

    def test_loader_keeps_unicode_line_separator_inside_a_json_string(self):
        pairs = PAIRS_JSONL.read_bytes().replace(
            b'"fail":"dl-drop-cachekey-handoff"',
            b'"fail":"dl-drop\\u2028cachekey-handoff"',
            1,
        )
        with _fixture(pairs=pairs) as dest:
            rows = leftover6_catalog._load_jsonl(dest / "pairs.jsonl")
            self.assertEqual(rows[0]["fail"], "dl-drop\u2028cachekey-handoff")
            with self.assertRaisesRegex(CatalogError, "pinned row content"):
                load_catalog(dest)

    def test_middle_row_content_is_sealed_without_archive_refs(self):
        for filename, index, field in (("pairs.jsonl", 7, "fail"),
                                       ("pairs.jsonl", 22, "docs"),
                                       ("plants.jsonl", 31, "dump")):
            with self.subTest(field=field):
                rows = [json.loads(line) for line in (CONFIG_DIR / filename).read_text().splitlines()]
                rows[index][field] += " altered"
                key = "pairs" if filename == "pairs.jsonl" else "plants"
                with _fixture(**{key: dumps_jsonl(rows)}) as dest:
                    with self.assertRaisesRegex(CatalogError, "pinned row content"):
                        load_catalog(dest)

    def test_vendor_extension_is_case_insensitive(self):
        for name in ("mill_gql_leftover6_r260.PY", "SBOX-MILL-PLANTS-LEFTOVER6.Py"):
            with self.subTest(name=name), self.assertRaises(SystemExit):
                refuse_vendor_paths([name])

    def test_loader_refuses_stale_declared_totals(self):
        header = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        header["n_pair_rows_committed"] += 1
        with _fixture(header=json.dumps(header)) as dest:
            with self.assertRaisesRegex(CatalogError, "n_pair_rows_committed"):
                load_catalog(dest)

    def test_loader_refuses_duplicate_or_gapped_pair_rows(self):
        rows = _catalog_rows()
        rows[1]["slug"] = rows[0]["slug"]
        with _fixture(pairs=dumps_jsonl(rows)) as dest:
            with self.assertRaisesRegex(CatalogError, "duplicate identities"):
                load_catalog(dest)
        rows[1]["slug"] = "unique-test-slug"
        rows[1]["round"] += 1
        with _fixture(pairs=dumps_jsonl(rows)) as dest:
            with self.assertRaisesRegex(CatalogError, "not contiguous"):
                load_catalog(dest)


class Leftover6LegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("the immutable leftover6 source commit is not fetched")
        pair_rows = []
        plant_rows = []
        for mill in CATALOG.catalogs:
            live = _extract_live_source(mill)
            self.assertEqual(live["blob_sha"], mill.source_blob_sha1, mill.source_path)
            _append_live_rows(live, mill, pair_rows, plant_rows)
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
