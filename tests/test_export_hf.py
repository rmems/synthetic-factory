#!/usr/bin/env python3
"""Tests for the lossless curated export, viewer projection, and split files."""

import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parents[0]
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(REPO / "pipelines"))

import compose_curated  # noqa: E402
import export_hf  # noqa: E402
import verify_hf_release  # noqa: E402

from test_compose_curated import build_source_run, thalamic, write_jsonl  # noqa: E402

HAS_PYARROW = importlib.util.find_spec("pyarrow") is not None


def compose_fixture(root):
    """Compose the shared four-factory fixture and return the curated root."""

    source = build_source_run(Path(root) / "run")
    curated = Path(root) / "curated"
    compose_curated.compose_run(source, curated)
    return curated


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


class ExportHf(unittest.TestCase):
    def test_exports_payload_viewer_splits_and_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            provenance = export_hf.export_run(curated, root / "export")
            export = root / "export"

            self.assertTrue(provenance["training_ready"])
            self.assertEqual(provenance["audit"]["blockers"], [])
            self.assertEqual(provenance["records"], 7)
            self.assertIs(provenance["payload_published"], False)
            self.assertIs(provenance["trainer_launched"], False)
            self.assertEqual(
                provenance["compose"]["compose_version"],
                compose_curated.COMPOSE_VERSION,
            )

            # Curated payload is copied byte-identically, one file per source.
            for entry in provenance["files"]:
                copied = export / entry["path"]
                original = (
                    curated
                    / compose_curated.RECORDS_DIRNAME
                    / entry["path"].split(f"{export_hf.CURATED_DIRNAME}/", 1)[1]
                )
                self.assertEqual(copied.read_bytes(), original.read_bytes())
                self.assertEqual(
                    entry["sha256"], hashlib.sha256(copied.read_bytes()).hexdigest()
                )

            # The viewer projection is lossless per file.
            viewer_bytes = (export / export_hf.VIEWER_PATH).read_bytes()
            rows = export_hf.read_viewer_parquet(viewer_bytes)
            self.assertEqual(len(rows), provenance["records"])
            by_file = {}
            for row in rows:
                by_file.setdefault(row.source_file, []).append(row)
            for source_file, file_rows in by_file.items():
                self.assertEqual(
                    [row.source_line for row in file_rows],
                    list(range(1, len(file_rows) + 1)),
                )
                rebuilt = "".join(row.record_json + "\n" for row in file_rows)
                self.assertEqual(
                    rebuilt, (export / source_file).read_text(encoding="utf-8")
                )
            self.assertEqual(
                provenance["viewer"]["sha256"],
                hashlib.sha256(viewer_bytes).hexdigest(),
            )

            # Splits partition the corpus exactly once, with both sides present.
            train = (export / export_hf.TRAIN_PATH).read_text(encoding="utf-8").splitlines()
            evaluate = (export / export_hf.EVAL_PATH).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(train), provenance["splits"]["train_records"])
            self.assertEqual(len(evaluate), provenance["splits"]["eval_records"])
            self.assertTrue(train)
            self.assertTrue(evaluate)
            self.assertEqual(len(train) + len(evaluate), provenance["records"])
            self.assertEqual(set(train) & set(evaluate), set())
            self.assertEqual(
                sorted(train + evaluate), sorted(row.record_json for row in rows)
            )

            # The one-page protocol ships next to the splits and says "no trainer".
            protocol = (export / export_hf.PROTOCOL_PATH).read_text(encoding="utf-8")
            self.assertIn("# Evaluation protocol", protocol)
            self.assertIn("No trainer is launched", protocol)
            self.assertIn(export_hf.TRAIN_PATH, protocol)
            self.assertIn(export_hf.EVAL_PATH, protocol)
            self.assertEqual(
                provenance["splits"]["protocol_sha256"],
                hashlib.sha256(
                    (export / export_hf.PROTOCOL_PATH).read_bytes()
                ).hexdigest(),
            )

            stored = json.loads(
                (export / export_hf.PROVENANCE_PATH).read_text(encoding="utf-8")
            )
            self.assertEqual(stored, provenance)

    def test_refuses_a_corpus_that_is_not_training_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = root / "curated"
            records = curated / compose_curated.RECORDS_DIRNAME
            unidentified = thalamic("blocked")
            unidentified.pop("id")
            write_jsonl(
                records / "thalamic-trajectory-factory" / "batch-r01.jsonl",
                [unidentified, thalamic("other")],
            )

            with self.assertRaises(export_hf.ExportError) as caught:
                export_hf.export_run(curated, root / "export")
            self.assertIn("not training_ready", str(caught.exception))
            self.assertFalse((root / "export").exists())

    def test_refuses_curated_payload_that_is_not_canonical_jsonl(self):
        record = json.dumps(thalamic("payload"), ensure_ascii=False)
        broken = {
            "no trailing newline": record.encode("utf-8"),
            "blank line": (record + "\n\n" + record + "\n").encode("utf-8"),
            "invalid json": b'{"id": \n',
            "invalid utf-8": b"\xff\xfe\n",
        }
        for label, payload in broken.items():
            with self.subTest(label):
                with tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    factory = (
                        root
                        / "curated"
                        / compose_curated.RECORDS_DIRNAME
                        / "thalamic-trajectory-factory"
                    )
                    factory.mkdir(parents=True)
                    (factory / "batch-r01.jsonl").write_bytes(payload)
                    with self.assertRaises(export_hf.ExportError):
                        export_hf.export_run(root / "curated", root / "export")
                    self.assertFalse((root / "export").exists())

    def test_viewer_rows_keep_line_separators_inside_records(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            records = root / "curated" / compose_curated.RECORDS_DIRNAME
            factory = records / "thalamic-trajectory-factory"
            factory.mkdir(parents=True)
            # U+2028 is a line boundary for ``str.splitlines`` but not for JSONL.
            separator = "\u2028"
            first = thalamic("sep")
            first["state"]["domain"] = f"line{separator}separator"
            write_jsonl(factory / "batch-r01.jsonl", [first, thalamic("plain")])
            physical = (factory / "batch-r01.jsonl").read_text(encoding="utf-8")
            self.assertEqual(len(physical.splitlines()), 3)

            rows = export_hf.collect_rows(records)
            self.assertEqual([row.source_line for row in rows], [1, 2])
            self.assertEqual(
                json.loads(rows[0].record_json)["state"]["domain"],
                first["state"]["domain"],
            )

    def test_refuses_empty_missing_and_existing_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)

            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(root / "no-such-root", root / "export-a")

            empty = root / "empty-curated"
            (empty / compose_curated.RECORDS_DIRNAME).mkdir(parents=True)
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(empty, root / "export-b")

            export_hf.export_run(curated, root / "export")
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(curated, root / "export")
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(curated, curated / "nested-export")
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(curated, root / "missing-parent" / "export")

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

    def test_cli_prints_provenance_and_reports_refusals(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = export_hf.main([str(curated), str(root / "export")])
            self.assertEqual(status, 0)
            self.assertTrue(json.loads(stdout.getvalue())["training_ready"])

            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                status = export_hf.main([str(curated), str(root / "export")])
            self.assertEqual(status, 2)
            self.assertIn("refusing to overwrite", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
