#!/usr/bin/env python3
"""The viewer projection: Parquet round-trip, record framing, and splits."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from export_test_support import (  # noqa: E402
    HAS_PYARROW,
    compose_fixture,
)
from test_compose_curated import (  # noqa: E402
    thalamic,
    write_jsonl,
)
import compose_curated  # noqa: E402
import export_hf  # noqa: E402
import verify_hf_release  # noqa: E402


class ViewerParquet(unittest.TestCase):
    def test_round_trips_rows_through_the_stdlib_writer_and_reader(self):
        rows = [
            export_hf.ViewerRow("data/curated/f/a.jsonl", 1, '{"id":"one"}'),
            export_hf.ViewerRow("data/curated/f/a.jsonl", 2, '{"id":"twö","x":"漢"}'),
            export_hf.ViewerRow("data/curated/g/b.jsonl", 1, '{"id":"three"}'),
        ]
        payload = export_hf.write_viewer_parquet(rows)
        self.assertTrue(payload.startswith(b"PAR1"))
        self.assertTrue(payload.endswith(b"PAR1"))
        self.assertEqual(export_hf.read_viewer_parquet(payload), rows)

    def test_refuses_to_write_an_empty_projection(self):
        with self.assertRaises(export_hf.ExportError):
            export_hf.write_viewer_parquet([])

    def test_footer_satisfies_the_public_viewer_contract(self):
        rows = [export_hf.ViewerRow("data/curated/f/a.jsonl", 1, '{"id":"one"}')]
        payload = export_hf.write_viewer_parquet(rows)
        card = "---\nlicense: apache-2.0\n    num_examples: 1\n---\n"
        self.assertEqual(verify_hf_release._viewer_errors(card, payload), ())

    def test_rejects_truncated_and_foreign_payloads(self):
        payload = export_hf.write_viewer_parquet(
            [export_hf.ViewerRow("data/curated/f/a.jsonl", 1, "{}")]
        )
        for broken in (b"", b"NOPE" + payload[4:], payload[:-4]):
            with self.assertRaises(ValueError):
                export_hf.read_viewer_parquet(broken)

    @unittest.skipUnless(HAS_PYARROW, "pyarrow is not installed")
    def test_pyarrow_reads_the_projection_with_string_columns(self):
        import pyarrow.parquet as pq  # noqa: PLC0415 - optional test dependency

        rows = [
            export_hf.ViewerRow("data/curated/f/a.jsonl", 1, '{"id":"one"}'),
            export_hf.ViewerRow("data/curated/f/a.jsonl", 2, '{"id":"two"}'),
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "records.parquet"
            path.write_bytes(export_hf.write_viewer_parquet(rows))
            table = pq.read_table(path)

        self.assertEqual(table.num_rows, 2)
        self.assertEqual(table.column_names, list(export_hf.VIEWER_COLUMNS))
        self.assertEqual(str(table.schema.field("source_file").type), "string")
        self.assertEqual(str(table.schema.field("source_line").type), "int64")
        self.assertEqual(
            table.to_pylist(),
            [
                {
                    "source_file": row.source_file,
                    "source_line": row.source_line,
                    "record_json": row.record_json,
                }
                for row in rows
            ],
        )


class ExportViewerRecordFraming(unittest.TestCase):
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

            rows = export_hf.collect_rows(records)
            self.assertEqual([row.source_line for row in rows], [1, 2])
            self.assertEqual(
                json.loads(rows[0].record_json)["state"]["domain"],
                first["state"]["domain"],
            )


class ExportSplitDeterminism(unittest.TestCase):
    def test_split_is_deterministic_and_salt_sensitive(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            first = export_hf.export_run(curated, root / "export-a")
            second = export_hf.export_run(curated, root / "export-b")
            self.assertEqual(first["splits"]["train"], second["splits"]["train"])
            self.assertEqual(first["splits"]["eval"], second["splits"]["eval"])

            rows = export_hf.collect_rows(curated / compose_curated.RECORDS_DIRNAME)
            _train, evaluate = export_hf.split_rows(
                rows, eval_fraction=0.5, salt="other-salt"
            )
            self.assertTrue(evaluate)
            with self.assertRaises(export_hf.ExportError):
                export_hf.split_rows(rows, eval_fraction=0, salt="s")
            with self.assertRaises(export_hf.ExportError):
                export_hf.split_rows(rows[:1], eval_fraction=0.1, salt="s")

    def test_every_multi_record_factory_appears_in_both_splits(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            rows = export_hf.collect_rows(curated / compose_curated.RECORDS_DIRNAME)
            train, evaluate = export_hf.split_rows(
                rows, eval_fraction=export_hf.DEFAULT_EVAL_FRACTION, salt="fixture-salt"
            )

            def factories(subset):
                return {row.source_file.split("/")[2] for row in subset}

            multi = {
                path
                for path in factories(rows)
                if sum(row.source_file.split("/")[2] == path for row in rows) >= 2
            }
            self.assertTrue(multi)
            self.assertTrue(multi.issubset(factories(train)))
            self.assertTrue(multi.issubset(factories(evaluate)))

    def test_singleton_per_factory_snapshots_use_a_deterministic_global_fallback(self):
        rows = [
            export_hf.ViewerRow("data/curated/a/r1.jsonl", 1, '{"id":"a"}'),
            export_hf.ViewerRow("data/curated/b/r1.jsonl", 1, '{"id":"b"}'),
        ]
        for bucket in (0.0, 0.99):
            with self.subTest(bucket=bucket), mock.patch.object(
                export_hf, "split_bucket", return_value=bucket
            ):
                first = export_hf.split_rows(rows, eval_fraction=0.1, salt="snapshot")
                second = export_hf.split_rows(rows, eval_fraction=0.1, salt="snapshot")
            self.assertEqual(first, second)
            train, evaluate = first
            self.assertEqual(len(train), 1)
            self.assertEqual(len(evaluate), 1)
            self.assertEqual(
                {(row.source_file, row.source_line) for row in train + evaluate},
                {(row.source_file, row.source_line) for row in rows},
            )


if __name__ == "__main__":
    unittest.main()
