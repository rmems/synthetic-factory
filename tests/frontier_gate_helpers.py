#!/usr/bin/env python3
"""Shared helpers for frontier execution-gate tests."""

import json
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import (  # noqa: E402
    stage_reservation,
    thalamic,
    thalamic_factory,
    write,
    write_marker_mode,
)
import round_txn  # noqa: E402


def _write_round(factory, round_number, record, spec=None):
    rr = f"{round_number:02d}"
    batch = factory / f"batch-r{rr}.jsonl"
    notes = factory / f"NOTES-r{rr}.md"
    write(batch, [record])
    notes.write_text("# Critique\n\nConcrete gap.\n\nNovel coverage: 42%\n")
    spec = spec or {}
    payload = {
        "version": spec.get("version", 1),
        "factory": factory.name,
        "round": round_number,
        "records": 1,
        "expected_records": 1,
        "commit_point": f"ROUND-r{rr}.complete.json",
        "files": [
            {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
            {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
        ],
    }
    if "verification" in spec:
        payload["execution_verification"] = spec["verification"]
    marker = factory / payload["commit_point"]
    marker.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_marker_mode(factory)
    return marker


class FrontierGateTestCaseMixin:
    """Reusable factory and interrupted-publish operations."""

    def factory(self, root):
        return thalamic_factory(root)


    def stage(self, reservation, records):
        return stage_reservation(reservation, records)


    def _mutate_complete_marker(self, factory, tag, mutator):
        reservation = round_txn.reserve(factory, 1, 1)
        self.stage(reservation, [thalamic(tag)])
        round_txn.publish(factory, 1, reservation["token"])
        marker = factory / "ROUND-r01.complete.json"
        payload = json.loads(marker.read_text())
        mutated = mutator(dict(payload))
        marker.write_text(json.dumps(mutated, indent=2, sort_keys=True) + "\n")
        return payload


    def _interrupt_publish(self, factory, reservation, records, reason=None):
        self.stage(reservation, records)
        with mock.patch.object(
            round_txn, "copy_verified_exclusive", side_effect=OSError("boom")
        ):
            with self.assertRaises(OSError):
                round_txn.publish(factory, 1, reservation["token"], reason)
        publishing = factory / "ROUND-r01.publishing.json"
        self.assertTrue(publishing.is_file())
        return publishing


    def _setup_retry_waiver(self, factory, tag):
        reservation = round_txn.reserve(factory, 1, 1)
        reason = "sensor replay pending; waived for this window"
        self._interrupt_publish(
            factory, reservation, [thalamic(tag, observable=False)], reason
        )
        return reservation, reason


    def _mutate_publishing_marker(self, factory, tag, mutator):
        reservation = round_txn.reserve(factory, 1, 1)
        publishing = self._interrupt_publish(factory, reservation, [thalamic(tag)])
        payload = json.loads(publishing.read_text())
        mutated = mutator(payload)
        publishing.write_text(json.dumps(mutated) + "\n")
        return reservation


    def _assert_retry_publish_rejected(self, factory, tag, mutator, regex):
        reservation = self._mutate_publishing_marker(factory, tag, mutator)
        with self.assertRaisesRegex(round_txn.TransactionError, regex):
            round_txn.publish(factory, 1, reservation["token"])
        self.assertFalse((factory / "ROUND-r01.complete.json").exists())
