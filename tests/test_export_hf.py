#!/usr/bin/env python3
"""Tests for the lossless curated export, viewer projection, and split files."""

import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parents[0]
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(REPO / "pipelines"))

import compose_curated  # noqa: E402
import export_hf  # noqa: E402
import verify_hf_release  # noqa: E402

from test_compose_curated import (  # noqa: E402
    build_source_run,
    episode,
    multi_agent,
    thalamic,
    write_jsonl,
)

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


class ExportPayloadAndProvenance(unittest.TestCase):
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
            self.assertIn("deterministic post-curation snapshot", protocol)
            self.assertIn("held out only from a future trainer", protocol)
            self.assertIn("not tuning-independent evidence for curation", protocol)
            self.assertNotIn("never touched by curation tuning", protocol)
            self.assertIn(export_hf.TRAIN_PATH, protocol)
            self.assertIn(export_hf.EVAL_PATH, protocol)
            self.assertIn("`meta.factory` value", protocol)
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


class ExportDestinationSafety(unittest.TestCase):
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

    def test_refuses_export_destinations_lexically_or_resolved_under_raw(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            safe = root / "safe"
            safe.mkdir()

            lexical = raw / ".." / ".." / "safe" / "lexical-export"
            with self.assertRaisesRegex(export_hf.ExportError, "immutable raw"):
                export_hf.export_run(curated, lexical)
            self.assertFalse((safe / "lexical-export").exists())

            raw_link = root / "raw-link"
            raw_link.symlink_to(raw, target_is_directory=True)
            with self.assertRaisesRegex(export_hf.ExportError, "immutable raw"):
                export_hf.export_run(curated, raw_link / "resolved-export")
            self.assertFalse((raw / "resolved-export").exists())

            real_parent = root / "real-destination-parent"
            real_parent.mkdir()
            symlink_parent = root / "destination-parent-alias"
            symlink_parent.symlink_to(real_parent, target_is_directory=True)
            with self.assertRaisesRegex(
                export_hf.ExportError, "exact non-symlink"
            ):
                export_hf.export_run(curated, symlink_parent / "export")
            self.assertFalse((real_parent / "export").exists())

    def test_destination_parent_swap_cannot_redirect_creation_or_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            parent = root / "destination-parent"
            parent.mkdir()
            moved_parent = root / "original-parent-moved"
            destination = parent / "export"
            raw = root / "outputs" / "raw"
            real_mkdir = os.mkdir
            swapped = False

            def swap_parent_before_create(path, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if path == destination.name and dir_fd is not None and not swapped:
                    swapped = True
                    parent.rename(moved_parent)
                    raw.mkdir(parents=True)
                    parent.symlink_to(raw, target_is_directory=True)
                return real_mkdir(path, mode, dir_fd=dir_fd)

            with mock.patch.object(
                compose_curated.os,
                "mkdir",
                side_effect=swap_parent_before_create,
            ):
                with self.assertRaisesRegex(
                    export_hf.ExportError,
                    "destination parent changed while it was pinned",
                ):
                    export_hf.export_run(curated, destination)

            self.assertTrue(swapped)
            self.assertFalse((moved_parent / destination.name).exists())
            self.assertFalse((raw / destination.name).exists())
            self.assertFalse(destination.exists())


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


class ExportSourceReplayAuthentication(unittest.TestCase):
    def test_compose_paths_digests_coordinates_and_sidecars_are_authenticated(self):
        mutations = (
            "output_digest",
            "manifest_digest",
            "sidecar_digest",
            "unsafe_output_path",
            "coordinated_manifest_coordinate",
            "coordinated_manifest_output_id",
            "malformed_sidecar_reference",
            "excluded_sidecar_reference",
            "boolean_compose_count",
            "coordinated_sidecar_content",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                curated = compose_fixture(root)
                summary_path = curated / compose_curated.SUMMARY_FILENAME
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                manifest_path = curated / summary["manifest"]["path"]
                sidecar_path = curated / summary["reward_sidecars"]["path"]

                if mutation == "output_digest":
                    output = curated / summary["outputs"][0]["path"]
                    payload = output.read_bytes()
                    output.write_bytes(payload.replace(b"\n", b" \n", 1))
                elif mutation == "manifest_digest":
                    manifest_path.write_bytes(manifest_path.read_bytes() + b" \n")
                elif mutation == "sidecar_digest":
                    sidecar_path.write_bytes(sidecar_path.read_bytes() + b" \n")
                elif mutation == "unsafe_output_path":
                    summary["outputs"][0]["path"] = "../escaped.jsonl"
                    summary_path.write_text(
                        json.dumps(summary, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                elif mutation == "coordinated_manifest_coordinate":
                    documents = [
                        json.loads(line)
                        for line in manifest_path.read_text(encoding="utf-8").split("\n")
                        if line
                    ]
                    retained = next(item for item in documents if item["action"] == "retained")
                    retained["output_sha256"] = "0" * 64
                    payload = "".join(
                        json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                        + "\n"
                        for item in documents
                    ).encode("utf-8")
                    manifest_path.write_bytes(payload)
                    summary["manifest"]["sha256"] = hashlib.sha256(payload).hexdigest()
                    summary_path.write_text(
                        json.dumps(summary, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                elif mutation in {
                    "coordinated_manifest_output_id",
                    "malformed_sidecar_reference",
                    "excluded_sidecar_reference",
                }:
                    documents = [
                        json.loads(line)
                        for line in manifest_path.read_text(encoding="utf-8").split("\n")
                        if line
                    ]
                    if mutation == "coordinated_manifest_output_id":
                        retained = next(
                            item for item in documents if item["action"] == "retained"
                        )
                        retained["output_id"] = "sfcur-forged"
                    elif mutation == "malformed_sidecar_reference":
                        retained = next(
                            item
                            for item in documents
                            if item["action"] == "retained"
                            and "reward_sidecar_id" in item
                        )
                        retained["reward_sidecar_id"] = []
                    else:
                        excluded = next(
                            item for item in documents if item["action"] == "excluded"
                        )
                        excluded["reward_sidecar_id"] = "0" * 64
                    payload = "".join(
                        json.dumps(
                            item,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n"
                        for item in documents
                    ).encode("utf-8")
                    manifest_path.write_bytes(payload)
                    summary["manifest"]["sha256"] = hashlib.sha256(payload).hexdigest()
                    summary_path.write_text(
                        json.dumps(summary, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                elif mutation == "boolean_compose_count":
                    summary["counts"]["excluded"] = True
                    summary_path.write_text(
                        json.dumps(summary, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                else:
                    documents = [
                        json.loads(line)
                        for line in sidecar_path.read_text(encoding="utf-8").split("\n")
                        if line
                    ]
                    documents[0]["classification"]["reason_codes"].append("tampered")
                    payload = "".join(
                        json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                        + "\n"
                        for item in documents
                    ).encode("utf-8")
                    sidecar_path.write_bytes(payload)
                    summary["reward_sidecars"]["sha256"] = hashlib.sha256(
                        payload
                    ).hexdigest()
                    summary_path.write_text(
                        json.dumps(summary, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )

                with self.assertRaises(export_hf.ExportError):
                    export_hf.export_run(curated, root / "export")
                self.assertFalse((root / "export").exists())

    def test_refuses_self_resealed_source_history_and_aggregate_claims(self):
        mutations = (
            "source_run_object",
            "source_run_lexical_alias",
            "source_digest_types",
            "fabricated_stages",
            "dropped_exclusion",
            "excluded_source_mapping",
            "fabricated_aggregates",
            "fabricated_calibration",
            "fabricated_compose_audit",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                curated = compose_fixture(root)
                summary_path = curated / compose_curated.SUMMARY_FILENAME
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                manifest_path = curated / summary["manifest"]["path"]
                documents = [
                    json.loads(line)
                    for line in manifest_path.read_text(encoding="utf-8").split("\n")
                    if line
                ]

                if mutation == "source_run_object":
                    summary["source_run"] = {"forged": True}
                elif mutation == "source_run_lexical_alias":
                    source_root = Path(summary["source_run"])
                    alias_parent = source_root.parent / "source-alias"
                    alias_parent.mkdir()
                    summary["source_run"] = (
                        f"{alias_parent.as_posix()}/../{source_root.name}"
                    )
                elif mutation == "source_digest_types":
                    documents[0]["source_sha256"] = []
                    documents[0]["source_file_sha256"] = False
                elif mutation == "fabricated_stages":
                    documents[0]["stages"] = [
                        {
                            "lane": "identity",
                            "transform_name": "forged",
                            "transform_version": "forged-v1",
                            "action": "retained",
                            "reason_codes": [],
                        }
                    ]
                elif mutation == "dropped_exclusion":
                    documents = [
                        entry for entry in documents if entry["action"] == "retained"
                    ]
                    summary["counts"]["source_records"] = len(documents)
                    summary["counts"]["excluded"] = 0
                    summary["exclusions"] = {}
                elif mutation == "excluded_source_mapping":
                    excluded = next(
                        entry for entry in documents if entry["action"] == "excluded"
                    )
                    excluded["source_path"] = "forged/batch-r99.jsonl"
                    excluded["source_line"] = 999
                    excluded["source_sha256"] = "f" * 64
                    excluded["source_file_sha256"] = "e" * 64
                elif mutation == "fabricated_aggregates":
                    summary["counts"]["source_files"] = 999
                    summary["lane_actions"] = {}
                    summary["exclusions"] = {"forged": 1}
                    summary["transforms"] = {"identity": {"name": "forged"}}
                elif mutation == "fabricated_calibration":
                    summary["calibration"] = {
                        "mode": "none",
                        "path": None,
                        "sha256": None,
                        "records": 1,
                    }
                    summary["calibrated_records"] = 1
                else:
                    summary["audit"]["training_ready"] = False
                    summary["audit"]["blockers"] = ["forged historical blocker"]

                if mutation in {
                    "source_digest_types",
                    "fabricated_stages",
                    "dropped_exclusion",
                    "excluded_source_mapping",
                }:
                    manifest_payload = "".join(
                        json.dumps(
                            entry,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n"
                        for entry in documents
                    ).encode("utf-8")
                    manifest_path.write_bytes(manifest_payload)
                    summary["manifest"]["entries"] = len(documents)
                    summary["manifest"]["sha256"] = hashlib.sha256(
                        manifest_payload
                    ).hexdigest()
                summary_path.write_text(
                    json.dumps(summary, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

                with self.assertRaises(export_hf.ExportError):
                    export_hf.export_run(curated, root / "export")
                self.assertFalse((root / "export").exists())


class ExportCompositionMemberSafety(unittest.TestCase):
    def test_rejects_symlink_and_hardlink_aliases_for_every_compose_member(self):
        mutations = (
            "summary_symlink",
            "manifest_symlink",
            "output_lexical_alias",
            "output_symlink",
            "output_hardlink",
            "source_symlink",
            "source_hardlink",
            "source_directory_symlink",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                curated = compose_fixture(root)
                summary_path = curated / compose_curated.SUMMARY_FILENAME
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                if mutation == "summary_symlink":
                    target = root / "outside-COMPOSE.json"
                    summary_path.replace(target)
                    summary_path.symlink_to(target)
                elif mutation == "manifest_symlink":
                    path = curated / summary["manifest"]["path"]
                    target = root / "outside-manifest.jsonl"
                    path.replace(target)
                    path.symlink_to(target)
                elif mutation == "source_symlink":
                    source_root = Path(summary["source_run"])
                    path = next(source_root.rglob("*.jsonl"))
                    target = root / "outside-source.jsonl"
                    path.replace(target)
                    path.symlink_to(target)
                elif mutation == "source_hardlink":
                    source_root = Path(summary["source_run"])
                    path = next(source_root.rglob("*.jsonl"))
                    target = root / "outside-source.jsonl"
                    path.replace(target)
                    os.link(target, path)
                elif mutation == "source_directory_symlink":
                    source_root = Path(summary["source_run"])
                    path = next(source_root.rglob("*.jsonl")).parent
                    target = root / "outside-source-directory"
                    path.replace(target)
                    path.symlink_to(target, target_is_directory=True)
                elif mutation == "output_lexical_alias":
                    summary["outputs"][0]["path"] = summary["outputs"][0][
                        "path"
                    ].replace("/", "//", 1)
                    summary_path.write_text(
                        json.dumps(summary, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                else:
                    path = curated / summary["outputs"][0]["path"]
                    target = curated / "aliased-output.bin"
                    path.replace(target)
                    if mutation == "output_symlink":
                        path.symlink_to(target)
                    else:
                        os.link(target, path)

                with self.assertRaises(export_hf.ExportError):
                    export_hf.export_run(curated, root / "export")
                self.assertFalse((root / "export").exists())


class ExportAuditByteCapture(unittest.TestCase):
    def test_audit_uses_captured_bytes_when_output_changes_before_the_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "multi-agent-coordination-factory"
            first = multi_agent("a")
            second = multi_agent("b")
            second["goal"] = "cover the TTL race before merge"
            second["transcript"][0]["content"] = "The race is real; stop the patch."
            second["joint_outcome"] = "reverted until the TTL test lands"
            records = [first, second]
            write_jsonl(source / "batch-r01.jsonl", records)
            curated = root / "curated"
            compose_curated.compose_run(root / "run", curated)
            output = (
                curated
                / compose_curated.RECORDS_DIRNAME
                / "multi-agent-coordination-factory"
                / "batch-r01.jsonl"
            )
            safe_payload = output.read_bytes()
            unsafe_documents = [
                json.loads(line)
                for line in safe_payload.decode("utf-8").split("\n")
                if line
            ]
            unsafe_documents[0]["thought"] = "hidden payload captured before the audit"
            unsafe_payload = "".join(
                compose_curated.canonical_json(record) + "\n"
                for record in unsafe_documents
            ).encode("utf-8")
            output.write_bytes(unsafe_payload)
            real_collect = export_hf.collect_files

            def capture_then_replace(records_dir):
                captured = real_collect(records_dir)
                output.write_bytes(safe_payload)
                return captured

            with mock.patch.object(
                export_hf, "collect_files", side_effect=capture_then_replace
            ):
                with self.assertRaisesRegex(export_hf.ExportError, "hidden-thought"):
                    export_hf.export_run(curated, root / "export")
            self.assertFalse((root / "export").exists())


class ExportCli(unittest.TestCase):
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
