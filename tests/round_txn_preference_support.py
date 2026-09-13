#!/usr/bin/env python3
"""Shared fixtures and helpers for the round-transaction preference tests.

Split out of ``test_round_txn`` so each test module states one
responsibility. Not named ``test_*`` so it is not itself collected.
"""

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import round_txn  # noqa: E402
import preference_arms  # noqa: E402

PREFERENCE_FIXTURES = REPO / "tests" / "fixtures" / "preference-arms"


def write_records(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def thalamic_factory(root):
    """The unrelated (non-preference) factory directory, for negative cases."""
    path = Path(root) / "outputs" / "raw" / "2099-01-01" / "thalamic-trajectory-factory"
    path.mkdir(parents=True)
    return path


def _fixture_records(fixture):
    return [
        json.loads(line)
        for line in (PREFERENCE_FIXTURES / fixture).read_text().splitlines()
        if line.strip()
    ]


def _drop_null_absence_markers(outcome):
    # "No incident" is an absent key, not a null one: the execution gate
    # reads a present ``incident``/``hazard_avoided`` as a claimed
    # observable event and refuses a null payload for it.
    for field in ("incident", "hazard_avoided"):
        if outcome.get(field, "") is None:
            del outcome[field]


def _declare_canonical_observables(outcome, arm_name):
    # main's publish gate runs verify_execution in strict mode and wants the
    # canonical observable trio. The committed arms carry domain observables
    # (compressor_read, doses_transferred) but not that shape, so declare it
    # here rather than editing the fixture's recorded evidence.
    outcome.setdefault("timeline", [{"t_ms": 0, "event": f"{arm_name} arm executed"}])
    outcome.setdefault("observed_effects", [f"{arm_name} arm outcome recorded"])
    outcome.setdefault(
        "new_state",
        {"sim_or_real": "designed", "domain": "transaction-test"},
    )


def _normalize_arm(record, arm_name, round_number):
    arm = record[arm_name]
    arm["id"] = arm["id"].replace("r11", f"r{round_number:02d}")
    outcome = arm.get("future_outcome")
    if isinstance(outcome, dict):
        _drop_null_absence_markers(outcome)
        _declare_canonical_observables(outcome, arm_name)


def ffpc_record(fixture="batch-r11.jsonl", round_number=1, index=0):
    record = _fixture_records(fixture)[index]
    record["id"] = record["id"].replace("r11", f"r{round_number:02d}")
    record["goal"] = "repair one failed action without changing its context"
    for holder in (record, record["chosen"], record["rejected"]):
        holder["meta"]["round"] = round_number
        holder["meta"]["factory"] = round_txn.PREFERENCE_ISOLATION_FACTORY
        holder["meta"]["isolation"] = round_txn.PREFERENCE_TWO_SESSION
    for arm_name in ("chosen", "rejected"):
        _normalize_arm(record, arm_name, round_number)
    return record


def shared_context(record):
    """The two-key context block a diagnosis hands to Session B."""

    return {
        "state": record["chosen"]["state"],
        "proposed_action": record["chosen"]["proposed_action"],
    }


def rejected_scratch(record):
    """Session A's scratch failure artifact, before the launcher stamps it."""

    arm = json.loads(json.dumps(record["rejected"]))
    meta = arm.get("meta")
    if isinstance(meta, dict):
        for stamped in ("isolation", "round", "factory"):
            meta.pop(stamped, None)
    return arm


def diagnosis_document(index, *, root_cause=None, context=None):
    if context is None:
        context = {
            "state": {"sim_or_real": "designed", "case": index},
            "proposed_action": {"action": "hold", "case": index},
        }
    target = {"per_component": {"safety": 0.5, "task_progress": 0.25}, "total": 0.75}
    return (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        "```json\n"
        f"{json.dumps(context, sort_keys=True)}\n"
        "```\n\n"
        "## Root cause\n\n"
        f"{root_cause or f'The gate skipped the required check for case {index}.'}\n\n"
        "## Cascade effects\n\n"
        "The gate error propagated through execution, outcome, and reward.\n\n"
        "## Supervisor catch\n\n"
        "Require the missing evidence before allowing execution.\n\n"
        "## Repair sketch\n\n"
        "Add the bounded check and use the safe fallback on failure.\n\n"
        "## Target reward delta\n\n"
        "```json\n"
        f"{json.dumps(target, sort_keys=True)}\n"
        "```\n"
    )


class PreferenceRoundHarness(unittest.TestCase):
    """Staging and marker scaffolding shared by the FFPC test modules.

    Session A writes the rejected scratch artifacts and diagnoses, the
    verifier binds them, and only then does Session B's batch appear -- the
    order the publisher's bindings depend on.
    """

    def factory(self, root):
        path = (
            Path(root) / "outputs" / "raw" / "2099-01-01" / round_txn.PREFERENCE_ISOLATION_FACTORY
        )
        path.mkdir(parents=True)
        return path

    def reserve(self, factory, round_number=1):
        return round_txn.reserve(
            factory,
            round_number,
            round_txn.FACTORY_QUOTAS[round_txn.PREFERENCE_ISOLATION_FACTORY],
            round_txn.PREFERENCE_TWO_SESSION,
        )

    def fill_stage(self, reservation, record, *, include_handoff=True, diagnoses=None):
        """Stage one round the way Session A then Session B would write it.

        ``diagnoses`` maps a diagnosis number to keyword overrides for its
        document, so a test can stage one that does not describe the pair it
        is published beside, or whose prose the chosen arm copied.
        """
        stage = Path(reservation["staging_dir"])
        round_number = reservation["round"]
        records = [
            record,
            ffpc_record(round_number=round_number, index=1),
            ffpc_record(round_number=round_number, index=2),
        ]
        scratch_names = preference_arms.rejected_scratch_filenames(round_number, len(records))
        for scratch_name, staged in zip(scratch_names, records, strict=True):
            (stage / scratch_name).write_text(
                json.dumps(rejected_scratch(staged)), encoding="utf-8"
            )
        if include_handoff:
            names = preference_arms.diagnosis_filenames(round_number, len(records))
            for index, (name, staged) in enumerate(zip(names, records, strict=True), 1):
                overrides = {
                    "context": shared_context(staged),
                    **(diagnoses or {}).get(index, {}),
                }
                (stage / name).write_text(
                    diagnosis_document(index, **overrides), encoding="utf-8"
                )
            preference_arms.write_diagnosis_handoff_receipt(stage, names)
        write_records(stage / reservation["batch_file"], records)
        (stage / reservation["notes_file"]).write_text(
            "# Critique\n\nIndependent arms were checked before publication.\n"
            "\nNovel coverage: 42%\n"
        )
        return stage

    def write_v1_completion(self, factory, round_number=1, *, version=1):
        batch = factory / f"batch-r{round_number:02d}.jsonl"
        notes = factory / f"NOTES-r{round_number:02d}.md"
        write_records(batch, [ffpc_record(round_number=round_number)])
        notes.write_text("# Critique\n\nHistorical pre-v2 preference evidence.\n")
        marker = factory / f"ROUND-r{round_number:02d}.complete.json"
        marker.write_text(
            json.dumps(
                {
                    "version": version,
                    "factory": factory.name,
                    "round": round_number,
                    "records": 1,
                    "expected_records": 1,
                    "commit_point": marker.name,
                    "files": [
                        {
                            "name": batch.name,
                            "sha256": round_txn.file_sha256(batch),
                        },
                        {
                            "name": notes.name,
                            "sha256": round_txn.file_sha256(notes),
                        },
                    ],
                }
            )
            + "\n"
        )
        return marker

    def stage_with_marker(self, factory, *, set_fields=None, drop_fields=()):
        """Reserve, rewrite the reservation marker, and stage a valid pair."""
        reservation = self.reserve(factory)
        marker = factory / "ROUND-r01.reserved.json"
        payload = json.loads(marker.read_text())
        for field in drop_fields:
            payload.pop(field)
        payload.update(set_fields or {})
        marker.write_text(json.dumps(payload) + "\n")
        self.fill_stage(reservation, ffpc_record())
        return reservation

    def staged_round_paths(self, factory):
        """Stage a valid pair; return its reservation, stage, and marker paths."""
        reservation = self.reserve(factory)
        stage = self.fill_stage(reservation, ffpc_record())
        return (
            reservation,
            stage,
            factory / "ROUND-r01.publishing.json",
            factory / "ROUND-r01.complete.json",
        )

    def assert_reserve_refused(self, factory, pattern):
        """Reserving a two-session preference round fails with ``pattern``."""
        with self.assertRaisesRegex(round_txn.TransactionError, pattern):
            round_txn.reserve(factory, 1, 1, round_txn.PREFERENCE_TWO_SESSION)

    def assert_publish_refused(self, factory, reservation, pattern):
        """Publication fails with ``pattern`` and commits no completion marker."""
        with self.assertRaisesRegex(round_txn.TransactionError, pattern):
            round_txn.publish(factory, 1, reservation["token"])
        self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def assert_recovery_state_preserved(self, factory, stage, publishing, complete):
        """A refused publish leaves the round retryable, not half-committed."""
        self.assertTrue(stage.is_dir())
        self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
        self.assertTrue(publishing.is_file())
        self.assertFalse(complete.exists())
