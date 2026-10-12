"""Every reachable refusal in the RLB catalog loader, driven through ``load_catalog``.

Each case copies the committed header and pair rows into a temporary directory,
applies one edit, and pins the exact ``CatalogError`` message the loader raises
today. Two guards are unreachable through the public loader and are not driven:
``_source`` cannot see an empty pair list (``_sources_with_pairs`` refuses it
first), and ``_refuse_duplicates`` cannot see a repeated record id without a
repeated round (the round is part of every id). CRLF framing is not driven either:
``Path.read_text`` translates newlines before the ``"\\r"`` check sees them.
"""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from pipelines.rlb import CATALOG_DIR, CatalogError, load_catalog

HEADER = json.loads((CATALOG_DIR / "CATALOG.json").read_text(encoding="utf-8"))
ROWS = tuple(
    json.loads(line)
    for line in (CATALOG_DIR / "pairs.jsonl").read_text(encoding="utf-8").splitlines()
)
FIRST_SOURCE = "experiments/rlb_leftover3_mill.py"
PAIR0 = "catalog.catalogs[0].pairs[0]"
IDENTITY = "catalog identity does not match the reviewed RLB family"
CATALOGS_LIST = "catalog.catalogs must be a non-empty list"
LOAD_FAILED = "cannot load RLB catalog "


def _pairs_text(rows):
    return "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows)


def _row_field(section, field, value):
    def edit(_header, rows):
        rows[0][section][field] = value

    return edit


def _row_value(key, value):
    def edit(_header, rows):
        rows[0][key] = value

    return edit


def _header_value(key, value):
    def edit(header, _rows):
        header[key] = value

    return edit


def _unchanged(_header, _rows):
    """Keep the committed header and rows as they are."""


def _shared_slug(_header, rows):
    rows[0]["handoff"]["slug"] = rows[0]["success"]["slug"]


def _gapped_round(_header, rows):
    rows[0]["round"] = 83


def _repeated_source(header, _rows):
    header["catalogs"][1] = copy.deepcopy(header["catalogs"][0])


def _unpaired_source(header, _rows):
    header["catalogs"][0]["source_path"] = "experiments/unpaired.py"


def _unknown_pair_source(_header, rows):
    rows[0]["source_path"] = "experiments/unknown.py"


def _overlapping_rounds(header, rows):
    second = header["catalogs"][1]
    second["start_round"], second["end_round"] = 82, 97
    second_rows = [row for row in rows if row["source_path"] == second["source_path"]]
    for offset, row in enumerate(second_rows):
        row["round"] = 82 + offset


# (label, edit(header, rows), exact CatalogError message)
EDIT_CASES = (
    ("case is not an object", _row_value("success", []), f"{PAIR0}.success must be an object"),
    ("blank slug", _row_field("success", "slug", " "),
     f"{PAIR0}.success.slug must be a non-empty string"),
    ("slug format", _row_field("success", "slug", "Bad_Slug"),
     f"{PAIR0}.success.slug has invalid format: 'Bad_Slug'"),
    ("module format", _row_field("handoff", "module", "mod-x"),
     f"{PAIR0}.handoff.module has invalid format: 'mod-x'"),
    ("coverage type", _row_field("success", "coverage", "80"),
     f"{PAIR0}.success.coverage must be an integer"),
    ("coverage bool", _row_field("handoff", "coverage", True),
     f"{PAIR0}.handoff.coverage must be an integer"),
    ("coverage floor", _row_field("success", "coverage", -1),
     f"{PAIR0}.success.coverage out of range: -1"),
    ("coverage ceiling", _row_field("handoff", "coverage", 101),
     f"{PAIR0}.handoff.coverage out of range: 101"),
    ("scalar type", _row_field("success", "expected_value", True),
     f"{PAIR0}.success.expected_value must be an integer or string"),
    ("scalar empty", _row_field("success", "naive_value", ""),
     f"{PAIR0}.success.naive_value must not be empty"),
    ("docs arity", _row_field("success", "docs", ["https://example.com"]),
     f"{PAIR0}.success.docs must contain exactly two URLs"),
    ("docs scheme", _row_field("handoff", "docs", ["https://a.example", "http://b.example"]),
     f"{PAIR0}.handoff.docs URLs must use https"),
    ("shared slug", _shared_slug, f"{PAIR0} repeats one slug on both outcomes"),
    ("round floor", _row_value("round", 0), f"{PAIR0}.round out of range: 0"),
    ("gapped rounds", _gapped_round,
     "catalog.catalogs[0] rounds are not contiguous across its declared range"),
    ("pair row keys", _row_value("extra", 1),
     "pairs.jsonl:1 keys differ: missing=[], extra=['extra']"),
    ("catalogs type", _header_value("catalogs", {}), CATALOGS_LIST),
    ("catalogs empty", _header_value("catalogs", []), CATALOGS_LIST),
    ("repeated source", _repeated_source, f"catalog repeats source {FIRST_SOURCE}"),
    ("unpaired source", _unpaired_source, "catalog.catalogs[0] has no pairs"),
    ("unknown pair source", _unknown_pair_source,
     "pairs.jsonl names unknown sources: ['experiments/unknown.py']"),
    ("schema version", _header_value("schema_version", "rlb-case-catalog-v0"),
     "unsupported schema version: 'rlb-case-catalog-v0'"),
    ("family", _header_value("family", "rlx"), IDENTITY),
    ("factory", _header_value("factory", "other-factory"), IDENTITY),
    ("generator", _header_value("generator", "grok-4.5"), IDENTITY),
    ("overlapping sources", _overlapping_rounds, "catalog repeats a round"),
)

# (label, CATALOG.json text or None for the committed header, pairs.jsonl text or None
#  for an absent file, message prefix)
FRAMING_CASES = (
    ("header is not JSON", "{", _pairs_text(ROWS), LOAD_FAILED),
    ("pairs file missing", None, None, LOAD_FAILED),
    ("pairs unterminated", None, _pairs_text(ROWS).rstrip("\n"),
     "pairs.jsonl must be LF-framed jsonl"),
    ("pairs blank line", None, _pairs_text(ROWS[:1]) + "\n", "pairs.jsonl:2 is empty"),
    ("pairs not JSON", None, "{nope}\n", "pairs.jsonl:1 is not JSON: "),
)


def _write_tree(dest, header_text, pairs_text):
    (dest / "CATALOG.json").write_text(header_text, encoding="utf-8")
    if pairs_text is not None:
        (dest / "pairs.jsonl").write_text(pairs_text, encoding="utf-8", newline="")


def _edited_tree(dest, edit):
    header = copy.deepcopy(HEADER)
    rows = copy.deepcopy(list(ROWS))
    edit(header, rows)
    _write_tree(dest, json.dumps(header), _pairs_text(rows))


class RlbLoaderRefusals(unittest.TestCase):
    def _refusal(self, dest):
        with self.assertRaises(CatalogError) as caught:
            load_catalog(dest)
        return str(caught.exception)

    def test_committed_copy_loads_from_a_directory_or_its_header_path(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)
            _edited_tree(dest, _unchanged)
            by_dir = load_catalog(dest)
            by_file = load_catalog(dest / "CATALOG.json")
        self.assertEqual(by_dir, by_file)
        self.assertEqual(len(list(by_dir.record_ids())), 128)

    def test_each_edit_raises_its_exact_refusal(self):
        for label, edit, message in EDIT_CASES:
            with self.subTest(label), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp)
                _edited_tree(dest, edit)
                self.assertEqual(self._refusal(dest), message)

    def test_header_and_jsonl_framing_refusals(self):
        committed = json.dumps(HEADER)
        for label, header_text, pairs_text, prefix in FRAMING_CASES:
            with self.subTest(label), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp)
                _write_tree(dest, header_text or committed, pairs_text)
                self.assertTrue(self._refusal(dest).startswith(prefix))


if __name__ == "__main__":
    unittest.main()
