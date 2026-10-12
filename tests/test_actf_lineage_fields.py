"""Pin ``actf.lineage``'s ``path.json`` field refusals: strings and ``version_count``.

Each required string must be a non-empty ``str`` and ``version_count`` a
non-negative int that is not a bool; anything else is refused with
``FINDING_PATH_JSON_INVALID`` and a message naming the lineage and the value.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from actf_test_support import cv, lineage

_DIR = "actf-r99--fields"
_VALID = {
    "path_key": _DIR,
    "original_path": "/tmp/actf/gen.py",
    "original_basename": "gen.py",
    "classification": "exact",
    "version_count": 0,
}


def _read(tmp: str, payload: dict) -> lineage.Lineage:
    listed = Path(tmp) / "recovered_sources" / "by-original-path" / _DIR
    listed.mkdir(parents=True)
    (listed / "path.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return lineage.read_lineage(listed)


class PathJsonFieldTests(unittest.TestCase):
    def test_a_valid_path_json_reads(self):
        with TemporaryDirectory() as tmp:
            read = _read(tmp, _VALID)
        self.assertEqual((read.path_key, read.version_count, read.versions), (_DIR, 0, ()))

    def test_required_strings_must_be_non_empty_strings(self):
        cases = (
            ("original_path", "", "''"),
            ("original_path", 7, "7"),
            ("original_basename", None, "None"),
        )
        for field, value, shown in cases:
            with self.subTest(field=field, value=value), TemporaryDirectory() as tmp:
                with self.assertRaises(cv.ActfRefusal) as caught:
                    _read(tmp, dict(_VALID, **{field: value}))
                self.assertEqual(caught.exception.code, cv.FINDING_PATH_JSON_INVALID)
                self.assertTrue(
                    caught.exception.message.endswith(f"{field} must be a non-empty string, got {shown}"),
                    caught.exception.message,
                )

    def test_version_count_must_be_a_non_negative_int(self):
        for value in (-1, True, 1.0, "1", None):
            with self.subTest(value=value), TemporaryDirectory() as tmp:
                with self.assertRaises(cv.ActfRefusal) as caught:
                    _read(tmp, dict(_VALID, version_count=value))
                self.assertEqual(caught.exception.code, cv.FINDING_PATH_JSON_INVALID)
                self.assertIn(f"{_DIR} version_count must be a non-negative int", caught.exception.message)


if __name__ == "__main__":
    unittest.main()
