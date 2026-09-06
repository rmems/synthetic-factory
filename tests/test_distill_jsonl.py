#!/usr/bin/env python3
"""Direct tests of the JSONL reader and writer (``distill_jsonl``): per-line
failure, duplicate keys, the recursion boundary and the overwrite refusal."""

import tempfile
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared test support, by bare name

from distill_contract_test_support import (  # noqa: E402
    minimal_record,
    oc,
    uncanonicalisable_records,
)


class JsonlHelpers(unittest.TestCase):
    def test_write_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.jsonl"
            oc.write_jsonl(path, [minimal_record()])
            with self.assertRaises(oc.ContractError):
                oc.write_jsonl(path, [minimal_record()])

    def test_a_non_finite_constant_is_a_parse_failure_not_a_value(self):
        # json.loads accepts bare NaN. Letting one through means the first
        # canonical re-serialisation raises and takes down the whole run.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nan.jsonl"
            path.write_text('{"id": "x", "value": NaN}\n{"id": "y"}\n')
            entries = oc.read_jsonl(path)
            self.assertEqual(len(entries), 2)
            self.assertIsNone(entries[0][1])
            self.assertEqual(entries[1][1], {"id": "y"})

    def test_infinity_is_also_a_parse_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inf.jsonl"
            path.write_text('{"id": "x", "value": Infinity}\n')
            self.assertIsNone(oc.read_jsonl(path)[0][1])

    def test_round_trip_and_parse_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.jsonl"
            oc.write_jsonl(path, [minimal_record()])
            with path.open("a", encoding="utf-8") as handle:
                handle.write("{not json\n")
            entries = oc.read_jsonl(path)
            self.assertEqual(len(entries), 2)
            self.assertIsInstance(entries[0][1], dict)
            self.assertIsNone(entries[1][1])


class JsonlDuplicateKeys(unittest.TestCase):
    """A duplicated object key is a per-line parse failure, never last-wins."""

    def read(self, payload: bytes) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_bytes(payload)
            return oc.read_jsonl(path)

    def test_a_duplicated_top_level_key_is_a_parse_failure(self):
        # json.loads keeps the last value silently, so a line carrying two
        # `result` objects used to validate, and be digested, as whichever
        # came last, while main's strict loaders reject the same bytes.
        self.assertEqual(self.read(b'{"a": 1, "a": 2}\n{"b": 3}\n'), [(1, None), (2, {"b": 3})])

    def test_a_duplicated_key_at_any_depth_is_a_parse_failure(self):
        payload = b'{"result": {"outcome": "fallback", "outcome": "fail_closed"}}\n'
        self.assertEqual(self.read(payload), [(1, None)])

    def test_the_reader_uses_the_shared_duplicate_key_rejector(self):
        # The hook is the repository's existing strict-parsing primitive
        # (export_contract, training_audit, load_strict_json), not a private
        # copy grown inside the reader.
        from oracle_grounded import distill_jsonl

        hook = distill_jsonl._reject_duplicate_object_keys
        self.assertEqual(hook.__name__, "reject_duplicate_object_keys")
        self.assertTrue(hook.__module__.endswith("tag_jsonutil"), hook.__module__)

    def test_the_parse_dialect_is_otherwise_unchanged(self):
        rows = self.read(b'{"x": 1.5, "n": 2, "s": "\xc3\xa9", "t": true}\n{"y": NaN}\n')
        self.assertEqual(rows[0], (1, {"x": 1.5, "n": 2, "s": "\u00e9", "t": True}))
        self.assertIsInstance(rows[0][1]["x"], float)
        self.assertEqual(rows[1], (2, None))


class JsonlPerLineBoundary(unittest.TestCase):
    """The reader fails per line, never per file, for a pathological line too."""

    def test_a_pathologically_nested_line_is_a_parse_failure_not_an_abort(self):
        # json.loads raises RecursionError on 200,000 '[', a RuntimeError,
        # so it escaped the reader's ValueError boundary and took the whole
        # file down instead of being reported as the one bad line it is.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_bytes(b"[" * 200_000 + b"\n" + b'{"ok": 1}\n')
            self.assertEqual(oc.read_jsonl(path), [(1, None), (2, {"ok": 1})])



class JsonlFraming(unittest.TestCase):
    """The advertised per-line decode failure and the empty write."""

    def test_an_undecodable_line_is_the_one_bad_record_it_is(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_bytes(b'\xff\xfe{"a": 1}\n{"b": 2}\n')
            self.assertEqual(oc.read_jsonl(path), [(1, None), (2, {"b": 2})])

    def test_writing_no_records_creates_an_empty_file_and_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.jsonl"
            self.assertEqual(oc.write_jsonl(path, []), 0)
            self.assertEqual(path.read_bytes(), b"")
            self.assertEqual(oc.read_jsonl(path), [])



class JsonlCanonicalBoundary(unittest.TestCase):
    """RoR-190-B1: a line that parses but cannot take the envelope's canonical form."""

    def test_a_lone_surrogate_escape_is_that_lines_parse_failure(self):
        # The bytes are plain ASCII, json.loads accepts the escape, and the
        # resulting string cannot be re-encoded as UTF-8: downstream digests
        # would raise, so the reader reports the line instead.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_bytes(b'{"id": "x", "mission": "bounded \\ud800 fixture"}\n{"id": "y"}\n')
            self.assertEqual(oc.read_jsonl(path), [(1, None), (2, {"id": "y"})])

    def test_writing_uncanonicalisable_content_is_a_contract_error_and_leaves_no_file(self):
        for name, record in uncanonicalisable_records().items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "batch.jsonl"
                with self.assertRaises(oc.ContractError) as caught:
                    oc.write_jsonl(path, [minimal_record(), record])
                self.assertIsNotNone(caught.exception.__cause__)
                self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
