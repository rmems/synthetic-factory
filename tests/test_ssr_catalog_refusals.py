#!/usr/bin/env python3
"""Fail-closed ``ssr.catalog.load_catalog`` refusals on doctored catalog copies."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from ssr.catalog import CATALOG, load_catalog  # noqa: E402
from ssr.catalog_extract import (  # noqa: E402
    catalog_json_path,
    pairs_jsonl_path,
)
from ssr import vocabulary as cv  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
