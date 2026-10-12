"""build_fix.py fails closed: each converted check refuses on bad input.

Pure checks take values; tree checks read a scratch immutable tree and a scratch
"current Hub" download. Offline: module roots are patched to scratch trees and
pyarrow is a stand-in (see skill_publish_test_support).
"""

import importlib
import json
import shutil
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
support = importlib.import_module("skill_publish_test_support")

FACTORY = support.FACTORY
NAME = support.NAME
REPO_ID = support.REPO_ID
RESEARCH_LICENSE = support.RESEARCH_LICENSE
jsonl = support.jsonl
record = support.record


class BuildFixPureChecksTests(support.ScriptChecks, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.bf = support.script("build_fix")
        self.error = self.bf.FixBundleCheckError

    def test_round_key_refuses_an_unparseable_name(self):
        self.assert_refuses(self.error, "NOTES-x.md", self.bf.round_key, "NOTES-x.md")

    def test_census_refuses_repeated_or_non_string_ids(self):
        for records in ([record("a"), record("a")], [record(None)]):
            with self.subTest(records=records):
                self.assert_refuses(self.error, "ids not unique", self.bf.census, records)

    def test_sub_once_refuses_zero_or_several_matches(self):
        for text, count in (("abc", 0), ("zz", 2)):
            with self.subTest(text=text):
                self.assert_refuses(
                    self.error, str(("label", count)), self.bf.sub_once, text, "z", "y", "label"
                )

    def test_release_count_patch_refuses_a_card_without_the_sentence(self):
        old = {"records": 1, "file_count": 1}
        self.assert_refuses(
            self.error, "release contains", self.bf._patch_release_counts, "no card", old, old
        )

    def test_rounds_patch_refuses_rule_wording_drift(self):
        with mock.patch.object(self.bf, "RULE_MD", "a rule the card does not state"):
            self.assert_refuses(
                self.error, "rule wording drift", self.bf._patch_rounds_bullets, "card",
                ["batch-r01.jsonl"],
            )

    def test_front_matter_refuses_a_card_without_a_fence(self):
        self.assert_refuses(
            self.error, "README does not open with a front-matter fence",
            self.bf.front_matter, "# no front matter\n",
        )

    def test_viewer_checks_refuse_each_projection_defect(self):
        support.assert_viewer_defects_refused(self, self.bf, self.error, local_import=False)

    def test_stamp_checks_refuse_each_foreign_stamp(self):
        support.assert_stamp_defects_refused(self, self.bf._check_record_stamps, self.error)

    def test_old_snapshot_checks_refuse_each_mismatch(self):
        old = {"records": 2, "file_count": 1, "parquet_bytes": 10, "parquet_sha256": "ab"}
        good = {
            "selection_rule": self.bf.OLD_PROV_RULE,
            "records": 2,
            "files": [{}],
            "viewer": {"bytes": 10, "sha256": "ab"},
            "superseded_not_published": ["batch-r02.jsonl"],
        }
        self.bf._check_old_snapshot(good, old, ["batch-r02.jsonl"])
        defects = [
            ({"selection_rule": "other"},
             "provenance selection_rule is not the old supersede rule"),
            ({"records": 3}, "provenance record or file totals differ from the Hub files"),
            ({"files": []}, "provenance record or file totals differ from the Hub files"),
            ({"viewer": {"bytes": 11, "sha256": "ab"}},
             "provenance viewer size or digest differs from the Hub parquet"),
            ({"viewer": {"bytes": 10, "sha256": "cd"}},
             "provenance viewer size or digest differs from the Hub parquet"),
            ({"superseded_not_published": []},
             "provenance superseded_not_published differs from the derived omissions"),
        ]
        for change, message in defects:
            with self.subTest(change=change):
                self.assert_refuses(
                    self.error, message, self.bf._check_old_snapshot,
                    {**good, **change}, old, ["batch-r02.jsonl"],
                )

    def test_existing_file_entries_must_be_reproduced_exactly(self):
        entry = {"path": "data/raw/batch-r01.jsonl", "sha256": "ab", "records": 2}
        snap = {"files": [entry]}
        self.bf._check_existing_entries(snap, [entry, {"path": "data/raw/batch-r02.jsonl"}])
        self.assert_refuses(
            self.error, "data/raw/batch-r01.jsonl", self.bf._check_existing_entries,
            snap, [{**entry, "records": 3}],
        )

    def test_rewritten_snapshot_refuses_a_foreign_viewer_writer(self):
        snap = {"viewer": {"writer": "some other writer"}}
        self.assert_refuses(
            self.error, "provenance viewer writer is not the factory's export writer",
            self.bf._rewritten_snapshot, snap, {}, [],
        )

    def test_front_matter_delta_refuses_any_change_but_the_split_numbers(self):
        old = {"rows": 2, "parquet_bytes": 10}
        new = {"rows": 3, "parquet_bytes": 12}
        card = "---\na: 1\n    num_examples: {rows}\n    num_bytes: {parquet_bytes}\n---\nbody\n"
        self.bf._check_front_matter_delta(card.format(**old), card.format(**new), old, new)
        self.assert_refuses(
            self.error, "README front matter line count changed",
            self.bf._check_front_matter_delta,
            card.format(**old), card.format(**new).replace("a: 1\n", ""), old, new,
        )
        changed = card.format(**new).replace("a: 1", "a: 2")
        self.assert_refuses(
            self.error,
            str([
                ("a: 1", "a: 2"),
                ("    num_examples: 2", "    num_examples: 3"),
                ("    num_bytes: 10", "    num_bytes: 12"),
            ]),
            self.bf._check_front_matter_delta, card.format(**old), changed, old, new,
        )

    def test_card_wording_checks_refuse_each_stale_or_missing_statement(self):
        readme = "---\n" + RESEARCH_LICENSE + "---\n| `data/raw/batch-r02.jsonl` | 1 |\n"
        prov = {"raw_snapshot": {}}
        self.bf._check_card_wording(readme, "{}", prov, ["batch-r02.jsonl"])
        cases = [
            (readme.replace("license: other\n", ""), "{}", prov, [],
             "README front matter does not declare the research-only license"),
            (readme + "superseded\n", "{}", prov, [], "supersed"),
            (readme, '{"notes": "Supersession"}', prov, [], "Supersession"),
            (readme, "{}", {"note": "corrected re-emission"}, [], "corrected re-emission"),
            (readme, "{}", prov, ["batch-r03.jsonl"], "batch-r03.jsonl"),
        ]
        for card, rights_text, provenance, missing, message in cases:
            with self.subTest(message=message):
                self.assert_refuses(
                    self.error, message, self.bf._check_card_wording,
                    card, rights_text, provenance, missing,
                )

    def test_release_status_must_not_carry_a_count(self):
        cur = self.tmp / "cur"
        cur.mkdir()
        (cur / "release-status.json").write_text(json.dumps({"training_ready": False}))
        self.bf._check_release_status(cur)
        (cur / "release-status.json").write_text(json.dumps({"records": 4}))
        self.assert_refuses(
            self.error, "release-status.json carries a count", self.bf._check_release_status, cur
        )


class BuildFixTreeTests(support.ScriptChecks, unittest.TestCase):
    """Checks that read the immutable tree or the current Hub download."""

    def setUp(self):
        super().setUp()
        self.bf = support.script("build_fix")
        self.error = self.bf.FixBundleCheckError
        self.source = self.write_source_tree()
        self.enterContext(mock.patch.multiple(
            self.bf,
            SOURCE=self.tmp / "source",
            CURRENT=self.tmp / "current",
            FIX=self.tmp / "fix",
            RUN_FIX=self.tmp / "run-fix",
        ))
        self.cur = self.tmp / "current" / NAME

    def test_derive_missing_accepts_a_disjoint_pair(self):
        self.assertEqual(
            self.bf.derive_missing(FACTORY, ["batch-r01.jsonl", "batch-r02c.jsonl"]),
            (["batch-r02.jsonl"], []),
        )

    def test_derive_missing_refuses_a_c_file_without_its_base(self):
        (self.source / "batch-r02.jsonl").unlink()
        self.assert_refuses(
            self.error, "batch-r02.jsonl", self.bf.derive_missing, FACTORY, ["batch-r02c.jsonl"]
        )

    def test_derive_missing_refuses_a_c_file_that_is_not_on_the_hub(self):
        self.assert_refuses(self.error, "batch-r02c.jsonl", self.bf.derive_missing, FACTORY, [])

    def test_derive_missing_refuses_a_base_file_already_on_the_hub(self):
        self.assert_refuses(
            self.error, "batch-r02.jsonl", self.bf.derive_missing,
            FACTORY, ["batch-r02.jsonl", "batch-r02c.jsonl"],
        )

    def test_derive_missing_refuses_repeated_ids_inside_a_file(self):
        (self.source / "batch-r02c.jsonl").write_bytes(jsonl(record("c"), record("c")))
        self.assert_refuses(
            self.error, "repeated record ids inside batch-r02c.jsonl or batch-r02.jsonl",
            self.bf.derive_missing, FACTORY, ["batch-r02c.jsonl"],
        )

    def test_derive_missing_refuses_a_partial_id_overlap(self):
        (self.source / "batch-r02c.jsonl").write_bytes(jsonl(record("t-r02-0"), record("new")))
        self.assert_refuses(
            self.error, str((FACTORY, "batch-r02.jsonl", {"t-r02-0"})),
            self.bf.derive_missing, FACTORY, ["batch-r02c.jsonl"],
        )

    def test_load_rows_refuses_a_lossy_line_split(self):
        first_line = jsonl(record("t-r01-0")).decode().rstrip("\n")
        with mock.patch.object(
            support.strict_jsonl, "strict_lf_jsonl_lines", return_value=[first_line]
        ):
            self.assert_refuses(
                self.error, "batch-r01.jsonl", self.bf.load_rows, FACTORY, ["batch-r01.jsonl"]
            )

    def hub_raw(self, *names) -> Path:
        raw = self.cur / "data" / "raw"
        raw.mkdir(parents=True)
        for name in names:
            shutil.copyfile(self.source / name, raw / name)
        return raw

    def test_current_raw_names_refuses_a_name_outside_the_c_suffix_rule(self):
        raw = self.hub_raw("batch-r01.jsonl")
        (raw / "batch-r03b.jsonl").write_bytes(b"")
        self.assert_refuses(
            self.error, str(["batch-r01.jsonl", "batch-r03b.jsonl"]),
            self.bf._current_raw_names, FACTORY, self.cur,
        )

    def test_current_raw_names_refuses_a_hub_file_that_differs_from_the_source(self):
        raw = self.hub_raw("batch-r01.jsonl")
        (raw / "batch-r01.jsonl").write_bytes(jsonl(record("t-r01-0")))
        self.assert_refuses(
            self.error, "batch-r01.jsonl", self.bf._current_raw_names, FACTORY, self.cur
        )

    def test_current_raw_names_refuses_a_records_jsonl_viewer(self):
        self.hub_raw("batch-r01.jsonl")
        (self.cur / "data" / "viewer").mkdir()
        (self.cur / "data" / "viewer" / "records.jsonl").write_bytes(b"")
        self.assert_refuses(
            self.error, "unexpected records.jsonl", self.bf._current_raw_names, FACTORY, self.cur
        )

    def test_selection_refuses_unexpected_missing_or_duplicate_files(self):
        derived = (["batch-r02.jsonl"], [])
        with mock.patch.object(self.bf, "derive_missing", return_value=derived):
            self.assert_refuses(
                self.error, str((FACTORY, ["batch-r02.jsonl"], [])),
                self.bf._selection, FACTORY, [], [],
            )
        with mock.patch.object(self.bf, "derive_missing", return_value=([], ["batch-r09.jsonl"])):
            self.assert_refuses(
                self.error, str((FACTORY, ["batch-r09.jsonl"])),
                self.bf._selection, FACTORY, [], [],
            )

    def test_hub_viewer_must_be_reproduced_by_the_writer(self):
        self.hub_raw("batch-r01.jsonl")
        (self.cur / "data" / "viewer").mkdir()
        (self.cur / "data" / "viewer" / "records.parquet").write_bytes(b"not the writer's bytes")
        self.assert_refuses(
            self.error, "writer drift", self.bf._reproduce_hub_viewer,
            FACTORY, ["batch-r01.jsonl"], self.cur,
        )

    def test_copy_verbatim_refuses_a_copy_that_does_not_read_back(self):
        dest = self.tmp / "dest"
        dest.mkdir()
        with mock.patch.object(Path, "write_bytes", lambda path, data: path.write_text("x")):
            self.assert_refuses(
                self.error, "copy does not read back byte-identical: batch-r01.jsonl",
                self.bf._copy_verbatim, FACTORY, ["batch-r01.jsonl"], dest,
            )

    def test_current_provenance_refuses_a_non_canonical_serialization(self):
        self.cur.mkdir(parents=True)
        (self.cur / "provenance.json").write_text(json.dumps({"raw_snapshot": {}}))
        self.assert_refuses(
            self.error, "provenance serialization", self.bf._current_provenance, self.cur
        )

    def rights_target(self, text: str):
        self.cur.mkdir(parents=True)
        (self.tmp / "fix" / NAME).mkdir(parents=True)
        (self.cur / "rights.json").write_text(text)
        return self.bf._Target(FACTORY, REPO_ID, self.cur, self.tmp / "fix" / NAME, self.tmp)

    def test_rights_patch_refuses_a_record_without_the_old_sentence_once(self):
        target = self.rights_target(json.dumps({"notes": "no sentence here"}))
        self.assert_refuses(
            self.error, "rights.json does not carry the old c-file sentence exactly once",
            self.bf._write_rights, target,
        )

    def test_rights_patch_refuses_an_edit_outside_notes(self):
        sentence = self.bf.OLD_RIGHTS_SENTENCE
        target = self.rights_target(json.dumps({"notes": "n", "status_basis": sentence}))
        with mock.patch.object(support.rights_document, "load_rights_document_bytes"):
            self.assert_refuses(
                self.error, "rights.json changed outside notes", self.bf._write_rights, target
            )
        self.assertFalse((target.fix / "rights.json").exists())


if __name__ == "__main__":
    unittest.main()
