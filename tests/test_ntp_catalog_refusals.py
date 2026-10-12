#!/usr/bin/env python3
"""Fail-closed ``ntp.catalog.load_catalog`` refusals on doctored catalog copies."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from ntp import vocabulary as nv  # noqa: E402
from ntp.catalog import CATALOG, load_catalog  # noqa: E402
from ntp.catalog_extract import (  # noqa: E402
    catalog_json_path,
    leftover_jsonl_path,
    pairs_jsonl_path,
    mills_jsonl_path,
    themes_jsonl_path,
)


def _doctored_ntp_catalog(tmp: Path, *, header=None, **row_edits) -> Path:
    """Copy CATALOG.json and the four JSONL files into ``tmp`` after optional edits.

    ``row_edits`` maps ``mills`` / ``leftover`` / ``themes`` / ``pairs`` to a
    function that takes and returns that file's list of row dicts.
    """

    document = json.loads(catalog_json_path().read_text(encoding="utf-8"))
    if header is not None:
        header(document)
    (tmp / "CATALOG.json").write_text(json.dumps(document), encoding="utf-8")
    sources = {
        "mills": mills_jsonl_path(),
        "leftover": leftover_jsonl_path(),
        "themes": themes_jsonl_path(),
        "pairs": pairs_jsonl_path(),
    }
    for key, source in sources.items():
        text = source.read_text(encoding="utf-8")
        edit = row_edits.get(key)
        if edit is not None:
            rows = edit([json.loads(line) for line in text.splitlines()])
            text = "".join(
                json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n" for row in rows
            )
        (tmp / source.name).write_text(text, encoding="utf-8")
    return tmp / "CATALOG.json"


def _set_header(key: str, value):
    def apply(document):
        document[key] = value

    return apply


def _edit_first_row(**fields):
    def apply(rows):
        rows[0].update(fields)
        return rows

    return apply


def _edit_mill_row(mill_id: str, **fields):
    def apply(rows):
        for row in rows:
            if row["mill_id"] == mill_id:
                row.update(fields)
        return rows

    return apply


def _drop_rows(**match):
    def apply(rows):
        return [row for row in rows if any(row.get(k) != v for k, v in match.items())]

    return apply


class NtpLoadCatalogRefusalTests(unittest.TestCase):
    def assert_refused(self, message, **edits):
        with tempfile.TemporaryDirectory() as tmp:
            path = _doctored_ntp_catalog(Path(tmp), **edits)
            with self.assertRaisesRegex(ValueError, message):
                load_catalog(path)

    def test_unedited_copy_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            loaded = load_catalog(_doctored_ntp_catalog(Path(tmp)))
        self.assertEqual(loaded.n_pair_rows, CATALOG.n_pair_rows)
        self.assertEqual(set(loaded.mills), set(CATALOG.mills))

    def test_header_pins_are_checked(self):
        cases = (
            ("schema", "ntp-catalog-extract/v0", "schema is not ntp-catalog-extract/v1"),
            ("preserve_commit", "0" * 40, "preserve_commit drifted from vocabulary"),
            ("factory", "other-factory", "factory/generator drifted from vocabulary"),
            ("generator", "grok-0", "factory/generator drifted from vocabulary"),
            ("slice", "other", "slice drifted from vocabulary"),
            ("mills_filename", "m.jsonl", "mills_filename drifted from vocabulary"),
            ("leftover_filename", "l.jsonl", "leftover_filename drifted from vocabulary"),
            ("themes_filename", "t.jsonl", "themes_filename drifted from vocabulary"),
            ("pairs_filename", "p.jsonl", "pairs_filename drifted from vocabulary"),
            ("mills", {}, "must keep mill rows in mills.jsonl"),
        )
        for key, value, message in cases:
            with self.subTest(key=key):
                self.assert_refused(message, header=_set_header(key, value))

    def test_identity_row_kinds_and_mill_ids_are_checked(self):
        self.assert_refused(
            "leftover.jsonl:1 kind is not success or leftover",
            leftover=_edit_first_row(kind="other"),
        )
        self.assert_refused(
            "themes.jsonl:1 kind is not success or leftover",
            themes=_edit_first_row(kind="other"),
        )
        self.assert_refused(
            "themes.jsonl:1 mill_id is not a theme slice",
            themes=_edit_first_row(mill_id="ntp-mill-unique-lll"),
        )
        self.assert_refused(
            "pairs.jsonl:1 kind is not success or leftover",
            pairs=_edit_first_row(kind="other"),
        )
        self.assert_refused(
            "pairs.jsonl:1 mill_id is not a pair slice",
            pairs=_edit_first_row(mill_id=nv.THEME_MILL_ID),
        )

    def test_empty_theme_and_pair_buckets_are_refused(self):
        self.assert_refused(
            "themes.jsonl must include ntp-mill-r1326 success rows",
            themes=_drop_rows(kind="success"),
        )
        self.assert_refused(
            "themes.jsonl must include ntp-mill-r1326 leftover rows",
            themes=_drop_rows(kind="leftover"),
        )
        self.assert_refused(
            "pairs.jsonl must include rows for ntp-mill-unique-lll",
            pairs=_drop_rows(mill_id="ntp-mill-unique-lll", kind="leftover"),
        )

    def test_slice_counts_are_checked(self):
        cases = (
            (nv.SLICE_MILL_ID, "n_success", "leftover slice n_success does not match"),
            (nv.SLICE_MILL_ID, "n_leftover", "leftover slice n_leftover does not match"),
            (nv.THEME_MILL_ID, "n_success", "theme slice n_success does not match"),
            (nv.THEME_MILL_ID, "n_leftover", "theme slice n_leftover does not match"),
            (
                "ntp-mill-unique-lll",
                "n_success",
                "ntp-mill-unique-lll pair slice row counts drifted from mills.jsonl",
            ),
            (
                "ntp-mill-unique-lll",
                "n_leftover",
                "ntp-mill-unique-lll pair slice row counts drifted from mills.jsonl",
            ),
        )
        for mill_id, field, message in cases:
            with self.subTest(mill_id=mill_id, field=field):
                self.assert_refused(message, mills=_edit_mill_row(mill_id, **{field: 0}))

    def test_source_pins_are_checked(self):
        self.assert_refused(
            "ntp-mill-unique-lll pin disagrees with sources.py",
            mills=_edit_mill_row("ntp-mill-unique-lll", blob_sha="0" * 40),
        )
        self.assert_refused(
            "ntp-mill-unique-lll pin disagrees with sources.py",
            mills=_edit_mill_row("ntp-mill-unique-lll", path="experiments/x.py"),
        )
        self.assert_refused(
            r"catalog mills drifted from sources: extra=\[\] missing=\['ntp-mill-unique-lll'\]",
            mills=_drop_rows(mill_id="ntp-mill-unique-lll"),
        )


if __name__ == "__main__":
    unittest.main()
