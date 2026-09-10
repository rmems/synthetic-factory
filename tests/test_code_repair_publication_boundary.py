"""The generic execution waiver must never grant procedural admission."""
from __future__ import annotations

import json
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
