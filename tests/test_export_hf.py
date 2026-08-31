#!/usr/bin/env python3
"""The lossless curated export: payload, provenance, gating, and replay."""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from export_test_support import (  # noqa: E402
    compose_fixture,
)
from test_compose_curated import (  # noqa: E402
    build_source_run,
    episode,
    thalamic,
)
import compose_curated  # noqa: E402
import export_hf  # noqa: E402


class ExportPinnedWrites(unittest.TestCase):
    def test_refuses_a_split_directory_swapped_for_a_symlink(self):
        """A swapped ``data/splits`` must not divert exports into outputs/raw."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            destination = root / "export"
            destination.mkdir()
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            (destination / "data").mkdir()
            (destination / "data" / "splits").symlink_to(
                raw, target_is_directory=True
            )
            descriptor = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with self.assertRaises(export_hf.ExportError):
                    export_hf._write_new_bytes(
                        descriptor, export_hf.TRAIN_PATH, b"{}\n"
                    )
            finally:
                os.close(descriptor)
            self.assertEqual(sorted(path.name for path in raw.iterdir()), [])


class ExportPayloadAndProvenance(unittest.TestCase):
    def _assert_payload_copied_byte_identically(self, export, curated, provenance):
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

    def _assert_viewer_projection_lossless(self, export, provenance):
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

        return rows

    def _assert_splits_partition_once(self, export, provenance, rows):
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

    def _assert_protocol_and_provenance(self, export, provenance):
        # The one-page protocol ships next to the splits and says "no trainer".
        protocol = (export / export_hf.PROTOCOL_PATH).read_text(encoding="utf-8")
        self.assertIn("# Evaluation protocol", protocol)
        self.assertIn("No trainer is launched", protocol)
        self.assertIn("deterministic post-curation snapshot", protocol)
        self.assertIn("held out only from a future trainer", protocol)
        self.assertIn("not tuning-independent evidence for curation", protocol)
        self.assertNotIn("never touched by curation tuning", protocol)
        self.assertIn(export_hf.TRAIN_PATH, protocol)
        self.assertIn(export_hf.EVAL_PATH, protocol)
        self.assertIn("`meta.factory` value", protocol)
        # Codex #97 P2: preference wrappers may carry the factory only on
        # their sides, so the grouping instruction has to stay possible.
        self.assertIn("`chosen.meta.factory`", protocol)
        self.assertIn("`rejected.meta.factory`", protocol)
        self.assertNotIn("in `source_file`", protocol)
        self.assertIn(
            '`safety_decision.correctness == "incorrect"`',
            protocol,
        )
        self.assertIn("`meta.supervisor_error_type` is present", protocol)
        self.assertIn("rather than gold gate decisions", protocol)
        self.assertIn("`sign_order_only`: compare sign and order only", protocol)
        self.assertIn(
            "`exclude_from_reward_training`: omit reward-derived metrics",
            protocol,
        )
        self.assertEqual(
            provenance["splits"]["scope"],
            "post_curation_snapshot_future_trainer_holdout",
        )
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

    def test_exports_payload_viewer_splits_and_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            provenance = export_hf.export_run(curated, root / "export")
            export = root / "export"

            self.assertTrue(provenance["training_ready"])
            self.assertEqual(provenance["export_version"], "export-hf-v3")
            self.assertEqual(provenance["audit"]["blockers"], [])
            self.assertEqual(provenance["records"], 7)
            self.assertIs(provenance["payload_published"], False)
            self.assertIs(provenance["trainer_launched"], False)
            self.assertEqual(
                provenance["compose"]["compose_version"],
                compose_curated.COMPOSE_VERSION,
            )
            self._assert_payload_copied_byte_identically(export, curated, provenance)
            rows = self._assert_viewer_projection_lossless(export, provenance)
            self._assert_splits_partition_once(export, provenance, rows)
            self._assert_protocol_and_provenance(export, provenance)


class ExportSemanticDuplicateReplay(unittest.TestCase):
    def test_export_replays_pre_identity_semantic_duplicate_exclusions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            source_file = (
                source / "thalamic-trajectory-factory" / "batch-r01.jsonl"
            )
            duplicate = json.dumps(
                thalamic("a"),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            with source_file.open("a", encoding="utf-8") as handle:
                handle.write(duplicate + "\n")

            curated = root / "curated"
            summary = compose_curated.compose_run(source, curated)
            provenance = export_hf.export_run(curated, root / "export")
            train = (root / "export" / export_hf.TRAIN_PATH).read_text(
                encoding="utf-8"
            ).splitlines()
            evaluate = (root / "export" / export_hf.EVAL_PATH).read_text(
                encoding="utf-8"
            ).splitlines()

            self.assertEqual(
                summary["exclusions"][
                    compose_curated.REASON_DUPLICATE_SOURCE_RECORD
                ],
                1,
            )
            self.assertEqual(provenance["compose"]["source"]["records"], 9)
            self.assertEqual(provenance["records"], 7)
            self.assertEqual(len(train) + len(evaluate), 7)
            self.assertEqual(len(set(train + evaluate)), 7)

    def test_export_replays_post_curation_semantic_duplicate_exclusions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            source_file = (
                source
                / "agentic-coding-trajectory-factory"
                / "batch-r01.jsonl"
            )
            converged = episode("1")
            converged["steps"][0]["thought"] = "different hidden text"
            with source_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(converged) + "\n")

            curated = root / "curated"
            summary = compose_curated.compose_run(source, curated)
            provenance = export_hf.export_run(curated, root / "export")
            train = (root / "export" / export_hf.TRAIN_PATH).read_text(
                encoding="utf-8"
            ).splitlines()
            evaluate = (root / "export" / export_hf.EVAL_PATH).read_text(
                encoding="utf-8"
            ).splitlines()

            self.assertEqual(
                summary["exclusions"][
                    compose_curated.REASON_DUPLICATE_CURATED_RECORD
                ],
                1,
            )
            self.assertEqual(provenance["compose"]["source"]["records"], 9)
            self.assertEqual(provenance["records"], 7)
            self.assertEqual(len(train) + len(evaluate), 7)
            self.assertEqual(len(set(train + evaluate)), 7)


class ExportCorpusGating(unittest.TestCase):
    def test_refuses_a_corpus_that_is_not_training_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            blocked_report = {
                "training_ready": False,
                "blockers": ["adversarial audit blocker"],
                "totals": {"records": 7, "by_kind": {}},
            }

            with mock.patch.object(
                export_hf.training_audit, "audit_run", return_value=blocked_report
            ):
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


if __name__ == "__main__":
    unittest.main()
