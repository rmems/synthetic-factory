#!/usr/bin/env python3
"""Physical-LF framing regressions for check_records.check_jsonl."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PIPELINES = TESTS.parent / "pipelines"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import check_records  # noqa: E402
from check_records_test_helpers import _thalamic  # noqa: E402


class CheckRecordsPhysicalFraming(unittest.TestCase):
    def check_payload(self, payload):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "batch.jsonl"
            path.write_bytes(payload)
            return check_records.check_jsonl(path, path.name)

    def test_bare_cr_between_objects_is_not_a_record_boundary(self):
        payload = (
            json.dumps(_thalamic(id="first")) + "\r" + json.dumps(_thalamic(id="second")) + "\n"
        ).encode("utf-8")

        errors, warnings, kinds, records = self.check_payload(payload)

        self.assertTrue(any("JSON parse error" in error for error in errors), errors)
        self.assertEqual(warnings, [])
        self.assertEqual(kinds, {})
        self.assertEqual(records, 0)

    def test_crlf_is_a_supported_physical_record_boundary(self):
        lines = [
            json.dumps(_thalamic(id="first")),
            json.dumps(_thalamic(id="second")),
        ]

        errors, warnings, kinds, records = self.check_payload(
            ("\r\n".join(lines) + "\r\n").encode("utf-8")
        )

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(kinds, {"thalamic": 2})
        self.assertEqual(records, 2)

    def test_unicode_line_separators_remain_json_string_data(self):
        record = _thalamic(id="unicode-separators")
        record["state"]["domain"] = "left\u2028middle\u2029right"
        payload = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")

        errors, warnings, kinds, records = self.check_payload(payload)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(kinds, {"thalamic": 1})
        self.assertEqual(records, 1)


if __name__ == "__main__":
    unittest.main()
