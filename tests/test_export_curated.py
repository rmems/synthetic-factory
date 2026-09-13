#!/usr/bin/env python3
"""Exact curated-corpus reads: LF-only framing and lossless row projection."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parents[0]
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(REPO / "pipelines"))

from test_compose_curated import thalamic, write_jsonl  # noqa: E402
import compose_curated  # noqa: E402
import export_contract  # noqa: E402
import export_curated  # noqa: E402
import export_members  # noqa: E402


class ExportViewerRecordFraming(unittest.TestCase):
    def test_every_export_reader_rejects_crlf_as_non_lf_jsonl(self):
        payload = b'{"id":"one"}\r\n'
        readers = (
            lambda: export_members._lf_jsonl_documents(payload, "manifest.jsonl"),
            lambda: export_curated._read_curated_file(
                Path("unused.jsonl"), "factory/batch-r01.jsonl", payload=payload
            ),
        )

        for reader in readers:
            with self.subTest(reader=reader):
                with self.assertRaisesRegex(export_contract.ExportError, "LF-only"):
                    reader()

    def test_viewer_rows_keep_line_separators_inside_records(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            records = root / "curated" / compose_curated.RECORDS_DIRNAME
            factory = records / "thalamic-trajectory-factory"
            factory.mkdir(parents=True)
            # U+2028/U+2029 are boundaries for splitlines, but not for JSONL.
            separator = "\u2028middle\u2029"
            first = thalamic("sep")
            first["state"]["domain"] = f"line{separator}separator"
            write_jsonl(factory / "batch-r01.jsonl", [first, thalamic("plain")])
            physical = (factory / "batch-r01.jsonl").read_text(encoding="utf-8")
            self.assertGreater(len(physical.splitlines()), 2)

            rows = export_curated.collect_rows(records)
            self.assertEqual([row.source_line for row in rows], [1, 2])
            self.assertEqual(
                json.loads(rows[0].record_json)["state"]["domain"],
                first["state"]["domain"],
            )


if __name__ == "__main__":
    unittest.main()
