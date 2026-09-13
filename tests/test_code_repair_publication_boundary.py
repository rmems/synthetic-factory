"""The generic execution waiver must never grant procedural admission."""
from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from tests.test_round_txn import round_txn as rt


class ProceduralBoundaryTests(unittest.TestCase):
    def test_unmarked_procedural_jsonl_never_becomes_legacy_committed_data(self):
        for slug in ("python-function-repair-factory", "unknown-factory"):
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as directory:
                factory = Path(directory) / slug
                factory.mkdir()
                (factory / "batch-r01.jsonl").write_text(
                    json.dumps({"family": "python-function-repair", "id": "claim"}) + "\n")
                with self.assertRaisesRegex(rt.TransactionError, "procedural"):
                    rt.committed_jsonl_paths(factory)

    def test_procedural_summary_cannot_claim_verified_without_bound_evidence(self):
        from code_repair import publication
        summary = {"gate": publication.GATE, "strict": True, "semantics_version": 1,
                   "override": None, "counts": {"total": 1, "verified": 1,
                                                "failed": 0, "inconclusive": 0},
                   "procedural": {}, "fresh_replay": []}
        with self.assertRaisesRegex(rt.TransactionError, "procedural"):
            rt.validated_execution_verification_summary(summary)

    def test_transaction_refuses_wrong_path_and_mixed_family_before_validation(self):
        from tests.round_txn_test_helpers import thalamic, write_records
        for slug, records in (
            ("unknown-factory", [{"family": "python-function-repair", "id": "claim"}]),
            ("python-function-repair-factory", [
                {"family": "python-function-repair", "id": "claim"}, thalamic("foreign"),
            ]),
        ):
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as directory:
                factory = Path(directory) / "outputs/raw/2099-01-01" / slug
                factory.mkdir(parents=True)
                reservation = rt.reserve(factory, 1, len(records))
                stage = Path(reservation["staging_dir"])
                write_records(stage / reservation["batch_file"], records)
                (stage / reservation["notes_file"]).write_text("# Evidence\nOriginal run inputs.\n")
                with self.assertRaisesRegex(rt.TransactionError, "procedural"):
                    rt.publish(factory, 1, reservation["token"])

    def test_legacy_completion_version_cannot_hide_procedural_gate(self):
        from tests.round_txn_test_helpers import write_completion_marker, write_records
        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory) / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            write_records(batch, [{"family": "python-function-repair", "id": "claim"}])
            notes.write_text("# Evidence\nLegacy version is not procedural permission.\n")
            write_completion_marker(rt, factory, batch, notes)
            with self.assertRaisesRegex(rt.TransactionError, "procedural"):
                rt.completed_manifests(factory)

    def test_hosted_generator_claim_comes_from_loaded_reviewed_registry(self):
        from curate_identity import load_registry, FACTORY_REGISTRY_PATH
        import curate_identity
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = json.loads(FACTORY_REGISTRY_PATH.read_text())
            row = next(r for r in payload["factories"] if r["path_id"] == "cache-stampede-factory")
            row.update(generator="fable-5", generator_version="fable-5",
                       provider="anthropic", channel="consumer")
            path = root / "registry.json"
            path.write_text(json.dumps(payload))
            registry = load_registry(path)
            batch = root / "batch-r01.jsonl"
            batch.write_text(json.dumps({"meta": {"factory": row["path_id"], "round": 1,
                                                 "generator": "fable-5"}}) + "\n")
            with mock.patch.object(curate_identity, "_DEFAULT_REGISTRY", registry):
                errors = rt.validate_agentic_envelope(batch, root / row["path_id"], 1)
            self.assertFalse(any("meta.generator" in error for error in errors), errors)

    def test_direct_generic_execution_gate_cannot_waive_procedural_records(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory) / "batch-r01.jsonl"
            batch.write_text(json.dumps({"family": "python-function-repair", "id": "bad"}) + "\n")
            with self.assertRaisesRegex(rt.TransactionError, "procedural"):
                rt.execution_gate(batch, batch, override="Reviewed local evidence is sufficient")

    def test_procedural_route_refuses_hosted_batch_before_legacy_waiver(self):
        from tests.round_txn_test_helpers import thalamic, write_records
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            reservation = rt.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            write_records(stage / reservation["batch_file"], [thalamic("foreign-hosted")])
            (stage / reservation["notes_file"]).write_text("# Critique\nEvidence is independently reviewed.\n")
            with self.assertRaisesRegex(rt.TransactionError, "procedural"):
                rt.publish(factory, 1, reservation["token"],
                           execution_override="Reviewed local evidence is sufficient")


class PublicationInputBoundaryTests(unittest.TestCase):
    def test_candidate_parser_refuses_missing_and_duplicate_canonical_ids(self):
        from code_repair import publication

        cases = (
            (b"{}\n", "candidate lacks a canonical ID"),
            (b"[]\n", "candidate lacks a canonical ID"),
            (b'{"id":"same"}\n{"id":"same"}\n', "duplicate candidate ID"),
        )
        for payload, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(
                rt.TransactionError, message
            ):
                publication._records(payload)

    def test_round_input_refuses_each_malformed_capture_boundary(self):
        from code_repair import publication

        valid = {
            "format": publication.INPUT_FORMAT,
            "run_json": "{}",
            "candidates_jsonl": "",
            "lineage_cap": 1,
        }
        cases = (
            ([], "round-scoped input must be an object"),
            ({}, "invalid round-scoped input fields"),
            ({**valid, "format": "wrong"}, "invalid round-scoped input artifact"),
            ({**valid, "run_json": []}, "original run inputs must be exact UTF-8 strings"),
            ({**valid, "candidates_jsonl": []},
             "original run inputs must be exact UTF-8 strings"),
        )
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / publication.input_name(1)
            for value, message in cases:
                with self.subTest(message=message):
                    artifact.write_text(json.dumps(value))
                    with self.assertRaisesRegex(rt.TransactionError, message):
                        publication._load_input(artifact)

    def test_empty_selection_and_invalid_publish_requests_refuse_before_writes(self):
        from code_repair import publication

        with self.assertRaisesRegex(rt.TransactionError, "nonempty selected batch"):
            publication._selected_payload([], {})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = (
                (root / "wrong-factory", 1, "approved factory"),
                (root / "python-function-repair-factory", 0, "positive round number"),
            )
            for factory, round_number, message in cases:
                request = publication.PublishRequest(root / "run", factory, round_number)
                with self.subTest(message=message), self.assertRaisesRegex(
                    rt.TransactionError, message
                ):
                    publication.publish_run(
                        request
                    )
                self.assertFalse(factory.exists())

    def test_input_inspection_refuses_a_legacy_source_route(self):
        from code_repair import publication

        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory) / "legacy-factory"
            factory.mkdir()
            batch = factory / "batch-r01.jsonl"
            batch.write_text('{"id":"legacy"}\n')
            with self.assertRaisesRegex(rt.TransactionError, "procedural source route"):
                publication.inspect_inputs(factory, batch, 1)

    def test_fresh_gate_wraps_a_missing_captured_input_as_a_transaction_refusal(self):
        from code_repair import publication

        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory) / "python-function-repair-factory"
            factory.mkdir()
            batch = factory / "batch-r01.jsonl"
            batch.write_text('{"family":"python-function-repair","id":"candidate"}\n')
            with self.assertRaisesRegex(rt.TransactionError,
                                        r"code-repair-input-r01\.json"):
                publication.fresh_gate(factory, batch, 1)

    def test_missing_transaction_round_cannot_supply_a_completion_marker(self):
        from code_repair import publication_export

        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory) / "python-function-repair-factory"
            factory.mkdir()
            rt.ensure_marker_mode(factory)
            with self.assertRaisesRegex(rt.TransactionError, "completed round does not exist"):
                publication_export._completed_marker(factory / "ROUND-r01.complete.json")

    def test_sealed_export_inputs_refuse_unreadable_catalog_and_changed_license(self):
        from code_repair import admission, publication_export, vocabulary as cv

        trusted = admission.load_trusted_catalog()
        with tempfile.TemporaryDirectory() as directory:
            unreadable = replace(trusted, directory=Path(directory))
            with self.assertRaisesRegex(cv.RepairRefusal, "catalog became unreadable"):
                publication_export.trusted_export_catalog(unreadable)

        policy = dict(publication_export.sp.POLICY)
        policy["source_license_evidence"] = {
            **policy["source_license_evidence"],
            "license_sha256": "0" * 64,
        }
        with mock.patch.object(publication_export.sp, "POLICY", policy):
            with self.assertRaisesRegex(cv.RepairRefusal, "license bytes changed"):
                publication_export.attribution_files()


if __name__ == "__main__":
    unittest.main()
