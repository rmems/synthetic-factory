#!/usr/bin/env python3
"""PR-a: AST catalog extract and ``pipelines/ssr`` skeleton (no vendored mills)."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from ssr.catalog import CATALOG, load_catalog  # noqa: E402
from ssr.catalog_extract import (  # noqa: E402
    SHAPE_LITERAL,
    SHAPE_PLANT,
    SHAPE_S,
    SHAPE_TAILS,
    apply_inherited_scanners,
    catalog_document,
    catalog_json_path,
    deferred_pair_rows,
    dumps_catalog,
    dumps_pairs_jsonl,
    extract_companion_path,
    extract_mill_catalog,
    pairs_jsonl_path,
    summarize_catalog_records,
)
from ssr.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from ssr.sources import (  # noqa: E402
    MILL_SOURCES,
    catalog_sources,
    fast_sources,
    loop_sources,
)
from ssr import catalog_ast, vocabulary as cv  # noqa: E402

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
        self.assertEqual(len(extracted["pairs"]), 2)
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "trufflehog-bfd-map-leftover")
        self.assertEqual(extracted["pairs"][1]["success_slug"], "gitleaks-thinlto-leftover")

    def test_inherited_scan_expands_deferred_tail_pairs(self):
        parent = extract_mill_catalog(_TAILS_SNIPPET, path="experiments/ssr-mill-r436.py")
        child = extract_mill_catalog(
            'CATALOG_FIRST = 554\nTAILS = ["gold-map", "bfd-map", "thinlto", "ecl-fasl"]\n',
            path="experiments/ssr-mill-r554.py",
        )
        self.assertEqual(child["pairs"], [])
        rows = deferred_pair_rows([parent, child])
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[2]["mill_id"], "ssr-mill-r554")
        self.assertEqual(rows[2]["success_slug"], "gitleaks-gold-map-leftover")
        self.assertEqual(rows[2]["fail_slug"], "trufflehog-bfd-map-leftover")

    def test_pairs_jsonl_stays_compact(self):
        path = pairs_jsonl_path()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), cv.DEFERRED_PAIR_ROWS)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        mill_ids = set()
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            row = json.loads(line)
            self.assertEqual(tuple(row), cv.DEFERRED_PAIR_KEYS)
            mill_ids.add(row["mill_id"])
        self.assertNotIn(cv.SLICE_MILL_ID, mill_ids)
        self.assertEqual(len(mill_ids), 39)
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), cv.PAIRS_SHA256)

    def test_loader_fails_closed_on_a_missing_deferred_field(self):
        header = catalog_json_path().read_text(encoding="utf-8")
        lines = pairs_jsonl_path().read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        del first["fail_slug"]
        lines[0] = json.dumps(first, separators=(",", ":"))
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            (dest / "CATALOG.json").write_text(header, encoding="utf-8")
            (dest / "pairs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "keys drifted"):
                load_catalog(dest / "CATALOG.json")

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
        self.assertEqual(len(CATALOG.mills["ssr-mill-r1702"].pairs), 40)
        self.assertEqual(len(CATALOG.deferred_pairs), cv.DEFERRED_PAIR_ROWS)
        self.assertEqual(
            CATALOG.mills["ssr-mill-r197"].pairs[0]["success_slug"],
            "ripsecrets-third-party-glob",
        )


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
        self.assertEqual(
            dumps_pairs_jsonl(
                deferred_pair_rows(records, expected_rows=cv.DEFERRED_PAIR_ROWS)
            ),
            pairs_jsonl_path().read_text(encoding="utf-8"),
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



def _doctored_catalog(tmp: Path, edit_catalog=None, edit_pairs=None) -> Path:
    """Copy the committed catalog pair into ``tmp`` after optional edits."""

    document = json.loads(catalog_json_path().read_text(encoding="utf-8"))
    pairs_text = pairs_jsonl_path().read_text(encoding="utf-8")
    if edit_catalog is not None:
        edit_catalog(document)
    if edit_pairs is not None:
        pairs_text = edit_pairs(pairs_text)
    (tmp / "CATALOG.json").write_text(json.dumps(document), encoding="utf-8")
    if pairs_text is not None:
        (tmp / "pairs.jsonl").write_text(pairs_text, encoding="utf-8", newline="")
    return tmp / "CATALOG.json"


def _edit_first_pair_line(edit):
    def apply(text: str) -> str:
        lines = text.splitlines()
        lines[0] = edit(lines[0])
        return "\n".join(lines) + "\n"

    return apply


def _edit_pair_row(edit):
    def apply(line: str) -> str:
        row = json.loads(line)
        edit(row)
        return json.dumps(row, separators=(",", ":"), sort_keys=True)

    return _edit_first_pair_line(apply)


def _set_field(path: tuple[str, ...], value):
    def apply(document):
        target = document
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return apply


def _drop_mill(mill_id: str):
    def apply(document):
        del document["mills"][mill_id]

    return apply


def _add_empty_mill(document):
    row = dict(document["mills"]["ssr-mill-decoder"])
    row.update({"mill_id": "ssr-mill-extra", "n_rows": 0})
    document["mills"]["ssr-mill-extra"] = row


class SsrLoadCatalogRefusalTests(unittest.TestCase):
    def assert_refused(self, message, *, edit_catalog=None, edit_pairs=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = _doctored_catalog(Path(tmp), edit_catalog, edit_pairs)
            with self.assertRaisesRegex(ValueError, message):
                load_catalog(path)

    def test_unedited_copy_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            loaded = load_catalog(_doctored_catalog(Path(tmp)))
        self.assertEqual(loaded.n_pair_rows, CATALOG.n_pair_rows)
        self.assertEqual(set(loaded.mills), set(CATALOG.mills))

    def test_header_drift_is_refused(self):
        cases = (
            (("schema",), "ssr-catalog-extract/v0", "schema is not ssr-catalog-extract/v1"),
            (("preserve_commit",), "0" * 40, "preserve_commit drifted from vocabulary"),
            (("factory",), "other-factory", "factory/generator drifted from vocabulary"),
            (("generator",), "grok-0", "factory/generator drifted from vocabulary"),
            (("slice",), "r182", "slice drifted from vocabulary"),
        )
        for path, value, message in cases:
            with self.subTest(field=path[-1]):
                self.assert_refused(message, edit_catalog=_set_field(path, value))

    def test_extract_block_drift_is_refused(self):
        cases = (
            (("extract",), None, "extract.exec must be false"),
            (("extract", "exec"), True, "extract.exec must be false"),
            (("extract", "method"), "exec", "extract.method must be ast.parse"),
            (("extract", "source_files"), 76, "extract.source_files drifted"),
        )
        for path, value, message in cases:
            with self.subTest(field=".".join(path), value=value):
                self.assert_refused(message, edit_catalog=_set_field(path, value))

    def test_pairs_framing_is_refused(self):
        cases = (
            (lambda text: text.rstrip("\n"), "must be LF-framed jsonl"),
            (lambda text: "\n" + text, r"pairs.jsonl:1 is not a compact JSONL record"),
            (lambda text: " " + text, r"pairs.jsonl:1 is not a compact JSONL record"),
            (lambda text: "{" + text, r"pairs.jsonl:1 is not JSON"),
        )
        for edit, message in cases:
            with self.subTest(message=message):
                self.assert_refused(message, edit_pairs=edit)

    def test_missing_pairs_file_is_refused(self):
        self.assert_refused("cannot load SSR deferred pairs", edit_pairs=lambda text: None)

    def test_pair_row_schema_is_refused(self):
        self.assert_refused(
            r"pairs.jsonl:1.fail_slug must be a non-empty string",
            edit_pairs=_edit_pair_row(lambda row: row.update(fail_slug="")),
        )
        self.assert_refused(
            "keys drifted from deferred pair schema",
            edit_pairs=_edit_first_pair_line(lambda line: "[]"),
        )

    def test_pair_row_count_slice_and_digest_are_pinned(self):
        self.assert_refused(
            "pairs.jsonl has 1587 rows, expected 1588",
            edit_pairs=lambda text: "".join(text.splitlines(keepends=True)[1:]),
        )
        self.assert_refused(
            "pairs.jsonl must omit the committed r181 slice",
            edit_pairs=_edit_pair_row(lambda row: row.update(mill_id=cv.SLICE_MILL_ID)),
        )
        self.assert_refused(
            "pairs.jsonl sha256 drifted from vocabulary",
            edit_pairs=_edit_pair_row(lambda row: row.update(fail_slug="renamed")),
        )

    def test_mill_set_drift_is_refused(self):
        self.assert_refused(
            r"pairs.jsonl names unknown mills: \['ssr-mill-decoder'\]",
            edit_catalog=_drop_mill("ssr-mill-decoder"),
        )
        self.assert_refused(
            r"catalog mills drifted from sources: extra=\[\] missing=\['ssr-mill-r181'\]",
            edit_catalog=_drop_mill(cv.SLICE_MILL_ID),
        )
        self.assert_refused(
            r"catalog mills drifted from sources: extra=\['ssr-mill-extra'\] missing=\[\]",
            edit_catalog=_add_empty_mill,
        )

    def test_slice_row_drift_is_refused(self):
        self.assert_refused(
            "r181 slice must keep its 16 compact identities",
            edit_catalog=_set_field(("mills", cv.SLICE_MILL_ID, "pairs"), None),
        )
        self.assert_refused(
            "r181 slice n_rows does not match extracted pairs",
            edit_catalog=_set_field(("mills", cv.SLICE_MILL_ID, "n_rows"), 17),
        )
        self.assert_refused(
            "ssr-mill-r181 pin disagrees with sources.py",
            edit_catalog=_set_field(("mills", cv.SLICE_MILL_ID, "blob_sha"), "0" * 40),
        )

    def test_deferred_mill_drift_is_refused(self):
        decoder = ("mills", "ssr-mill-decoder")
        cases = (
            ("pairs", [{"success_slug": "x"}], "ssr-mill-decoder is not the first slice"),
            ("n_rows", 26, "ssr-mill-decoder deferred pairs 27 != n_rows 26"),
            ("first_slug", "x", "ssr-mill-decoder deferred first/last slug drifted"),
            ("last_slug", "x", "ssr-mill-decoder deferred first/last slug drifted"),
            ("path", "experiments/x.py", "ssr-mill-decoder deferred path drifted"),
            ("blob_sha", "0" * 40, "ssr-mill-decoder pin disagrees with sources.py"),
        )
        for field, value, message in cases:
            with self.subTest(field=field):
                self.assert_refused(message, edit_catalog=_set_field((*decoder, field), value))


class SsrCatalogAstTests(unittest.TestCase):
    @staticmethod
    def expr(source: str) -> ast.AST:
        return ast.parse(source, mode="eval").body

    def test_literal_value_resolves_names_and_expressions(self):
        env = {"A": "gitleaks", "N": 3}
        unset = catalog_ast.UNSET
        cases = (
            ("A", "gitleaks"),
            ("MISSING", unset),
            ("-N", -3),
            ("-2.5", -2.5),
            ("-A", unset),
            ("+N", unset),
            ("A + '-tail'", "gitleaks-tail"),
            ("A + N", unset),
            ("N - 1", unset),
            ("f'{A}-{N}'", "gitleaks-3"),
            ("f'{A!r}'", "gitleaks"),
            ("f'{MISSING}'", unset),
            ("f'{1.5}'", unset),
            ("{A, 'x'}", {"gitleaks", "x"}),
            ("{MISSING}", unset),
            ("{**A}", unset),
            ("{A: MISSING}", unset),
            ("[A, (N, 'x')]", ["gitleaks", (3, "x")]),
            ("A.upper()", unset),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(catalog_ast.literal_value(self.expr(source), env), expected)

    def test_ctor_identity_reads_keywords_and_s_positionals(self):
        cases = (
            ("plant(slug='a', scanner='gitleaks')", {"slug": "a", "scanner": "gitleaks"}),
            ("plant(scanner='gitleaks')", None),
            ("plant(slug=NAME)", None),
            ("S('a', 'gitleaks')", {"slug": "a", "scanner": "gitleaks"}),
            ("S(slug='k', scanner='t')", {"slug": "k", "scanner": "t"}),
            ("S('a')", {"slug": "a", "scanner": None}),
            ("S('a', NAME)", {"slug": "a", "scanner": None}),
            ("S(NAME, 'gitleaks')", None),
            ("other('a', 'b')", None),
            ("obj.plant(slug='a')", None),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(catalog_ast.ctor_identity(self.expr(source)), expected)

    def test_joined_path_and_spec_file_name(self):
        self.assertIsNone(extract_companion_path("MILL = ROOT\n"))
        self.assertIsNone(extract_companion_path('MILL = "a" / ROOT\n'))
        self.assertIsNone(extract_companion_path("MILL = ROOT.parent\n"))
        self.assertIsNone(extract_companion_path("OTHER = 'x'\n"))
        self.assertEqual(
            extract_companion_path('MILL = "experiments" / "x.py"\n'),
            "experiments/x.py",
        )
        loop = (
            "import importlib.util\n"
            'spec = importlib.util.spec_from_file_location("m")\n'
            'spec = importlib.util.spec_from_file_location("m", ROOT)\n'
            'spec = importlib.util.spec_from_file_location("m", ROOT / "ssr-mill-r9.py")\n'
        )
        extracted = extract_mill_catalog(loop, path="experiments/ssr-loop-r9.py")
        self.assertEqual(extracted["exec_target"], "ssr-mill-r9.py")
        self.assertEqual(extracted["kind"], cv.KIND_LOOP)


class SsrExtractRefusalTests(unittest.TestCase):
    def assert_unextractable(self, source: str):
        with self.assertRaisesRegex(ValueError, "has no extractable SSR catalog assignment"):
            extract_mill_catalog(source, path="experiments/ssr-mill-r9.py")

    def test_non_literal_dict_pairs_fall_through(self):
        self.assert_unextractable('PAIRS = [({"slug": NAME}, {"slug": "b"})]\n')

    def test_partially_constructed_pairs_fall_through(self):
        self.assert_unextractable(
            "PAIRS = [\n"
            '    (plant(slug="a", scanner="g"), plant(slug="b", scanner="t")),\n'
            '    (plant(scanner="x"), plant(slug="c")),\n'
            "]\n"
        )

    def test_bad_generated_rows_fall_through(self):
        for rows in (
            'ROWS = [("gitleaks", "a", 1)]',
            "ROWS = [NAME]",
            'ROWS = ["gitleaks"]',
            'ROWS = [("gitleaks",), ("t", "b")]',
            'ROWS = [(1, "a"), ("t", "b")]',
        ):
            with self.subTest(rows=rows):
                self.assert_unextractable(rows + "\n")

    def test_generated_rows_pair_successive_plants(self):
        extracted = extract_mill_catalog(
            'ROWS = [("gitleaks", "a", 1), ("trufflehog", "b", 2)]\n',
            path="experiments/ssr-mill-r9.py",
        )
        self.assertEqual(extracted["shape"], "rows-generated")
        self.assertEqual(extracted["catalog_first"], 9)
        self.assertEqual(extracted["first_slug"], "gitleaks-a")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "trufflehog-b")

    def test_later_non_literal_tails_and_scan_keep_the_last_literal(self):
        extracted = extract_mill_catalog(
            'SCAN = {"gitleaks": 1, "trufflehog": 2}\n'
            "SCAN = {NAME: 1}\n"
            'TAILS = ["a", "b"]\n'
            "TAILS = []\n"
            "TAILS = [1, 2]\n",
            path="experiments/ssr-mill-r9.py",
        )
        self.assertEqual(extracted["shape"], SHAPE_TAILS)
        self.assertEqual(extracted["scanners"], ["gitleaks", "trufflehog"])
        self.assertEqual(extracted["tails"], ["a", "b"])
        self.assertEqual(extracted["first_slug"], "gitleaks-a-leftover")

    def test_single_tail_is_unextractable(self):
        self.assert_unextractable('TAILS = ["a"]\n')

    def test_deferred_rows_refuse_a_pair_count_mismatch(self):
        record = {
            "kind": cv.KIND_PAIRS,
            "mill_id": "ssr-mill-r9",
            "path": "experiments/ssr-mill-r9.py",
            "shape": SHAPE_PLANT,
            "n_rows": 1,
            "pairs": [],
        }
        with self.assertRaisesRegex(ValueError, "ssr-mill-r9 deferred pairs 0 != n_rows 1"):
            deferred_pair_rows([record])
        with self.assertRaisesRegex(ValueError, "deferred pair rows 0 != pin 1"):
            deferred_pair_rows([], expected_rows=1)


class SsrInheritedScannerTests(unittest.TestCase):
    @staticmethod
    def tails_record(**overrides):
        record = {
            "shape": SHAPE_TAILS,
            "first_slug": None,
            "last_slug": None,
            "first_tail": "a",
            "last_success_tail": "c",
            "n_tails": 4,
            "tails": ["a", "b", "c", "d"],
            "scanners": [],
            "pairs": [],
        }
        record.update(overrides)
        return record

    def test_non_tails_record_is_returned_unchanged(self):
        record = {"shape": SHAPE_PLANT}
        self.assertIs(apply_inherited_scanners(record, ["gitleaks"]), record)

    def test_inherited_scanners_fill_slugs_and_pairs(self):
        filled = apply_inherited_scanners(self.tails_record(), ["gitleaks", "trufflehog"])
        self.assertEqual(filled["first_slug"], "gitleaks-a-leftover")
        self.assertEqual(filled["last_slug"], "gitleaks-c-leftover")
        self.assertEqual(len(filled["pairs"]), 2)

    def test_slug_fill_skips_incomplete_records(self):
        cases = (
            (self.tails_record(), []),
            (self.tails_record(first_tail=None, tails=None), ["gitleaks"]),
            (self.tails_record(n_tails=None, tails=None), ["gitleaks"]),
        )
        for record, scanners in cases:
            with self.subTest(record=record, scanners=scanners):
                self.assertIs(apply_inherited_scanners(record, scanners), record)

    def test_last_slug_needs_a_success_tail_and_two_tails(self):
        for overrides in ({"last_success_tail": None}, {"n_tails": 1}):
            with self.subTest(overrides=overrides):
                filled = apply_inherited_scanners(
                    self.tails_record(tails=["a"], **overrides), ["gitleaks"]
                )
                self.assertEqual(filled["first_slug"], "gitleaks-a-leftover")
                self.assertIsNone(filled["last_slug"])
                self.assertEqual(filled["pairs"], [])

    def test_local_scanners_win_and_existing_pairs_stay(self):
        local = apply_inherited_scanners(
            self.tails_record(first_slug="kept", scanners=["ggshield"]), ["gitleaks"]
        )
        self.assertEqual(local["first_slug"], "kept")
        self.assertEqual(local["pairs"][0]["success_scanner"], "ggshield")
        existing = self.tails_record(first_slug="kept", pairs=[{"success_slug": "p"}])
        self.assertIs(apply_inherited_scanners(existing, ["gitleaks"]), existing)


if __name__ == "__main__":
    unittest.main()
