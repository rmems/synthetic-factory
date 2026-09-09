"""Input bindings and family shapes checked before export projection or verdict derivation."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog
from . import generate
from . import lineage
from . import replay
from . import vocabulary as cv
from ._contract import bind_import_twin

_ROW = {"id": str, "status": str}
_PHASE = {"status": str, "load_ok": bool, "public": [_ROW], "hidden": [_ROW]}
_EXAMPLE = {"example_id": str, "source": str, "want": str}
_MODULE = {"files": {cv.PROGRAM_FILENAME: str}, "sha256": str}
_FAMILY_SHAPE = {
    "id": str,
    "scenario": {
        "task_specification": str,
        "source": {"program_id": str, "family": str, "module_sha256": str,
                   "upstream": {"function": str}},
        "broken_program": _MODULE,
        "public_tests": {"examples": [_EXAMPLE]},
    },
    "candidate_prediction": {"predicted_repair": _MODULE},
    "intervention": {"operator": str},
    "oracle": {"configuration": {"hidden_check": {"kind": str, "cases": [dict]}}},
    "result": {
        "outcome": str, "oracle_status": str, "reason_codes": [str],
        "broken_sha256": str, "repaired_sha256": str,
        "phases": {cv.PHASE_ORIGINAL: _PHASE, cv.PHASE_MUTANT: (_PHASE, type(None)),
                   cv.PHASE_REPAIRED: (_PHASE, type(None))},
        "public_failure_evidence": [{**_EXAMPLE, "got": str, "truncated": bool}],
        "public_failure_omitted": int,
    },
    "provenance": {"split_lineage": {
        "lineage_id": str, "group_id": (str, type(None)), "split": (str, type(None)),
        "policy_sha256": (str, type(None)),
    }},
}


def _shape(value: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return _object_shape(value, expected)
    if isinstance(expected, list):
        return isinstance(value, list) and all(_shape(v, expected[0]) for v in value)
    if isinstance(expected, tuple):
        return any(_shape(value, choice) for choice in expected)
    return type(value) is expected


def _object_shape(value: Any, fields: dict) -> bool:
    if not isinstance(value, dict):
        return False
    return all(key in value and _shape(value[key], shape) for key, shape in fields.items())


def family_shape(record: dict) -> bool:
    if not _shape(record, _FAMILY_SHAPE):
        return False
    reference = record["result"]["phases"].get(cv.PHASE_REFERENCE)
    return _shape(reference, (_PHASE, type(None)))


def _refuse(condition: bool, code: str) -> None:
    cv.refuse_when(condition, cv.FINDING_EXPORT_INTEGRITY, f"input fails integrity ({code})")


@dataclass(frozen=True)
class ReplayReport:
    status: str = "not run"
    entries: dict[str, dict] | None = None


def _read_report(path: Path) -> dict:
    cv.refuse_when(not path.is_file(), cv.FINDING_REPLAY_FILE_MISSING,
                   f"{cv.shown(path)} is missing")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise cv.RepairRefusal(
            cv.FINDING_EXPORT_INTEGRITY, cv.EXPORT_REPLAY_FILE_MALFORMED
        ) from exc
    _refuse(not _shape(report, {"format": str, "status": str, "records": [dict]}),
            cv.EXPORT_REPLAY_FILE_MALFORMED)
    _refuse(report["format"] != replay.REPLAY_FORMAT, cv.EXPORT_REPLAY_FILE_MALFORMED)
    return report


def _replay_entries(report: dict) -> dict[str, dict]:
    entries = {}
    for entry in report["records"]:
        _refuse(not _shape(entry, {"record_id": str, "status": str}),
                cv.EXPORT_REPLAY_FILE_MALFORMED)
        if entry["status"] == "replayed":
            _refuse(not isinstance(entry.get("code"), str), cv.EXPORT_REPLAY_FILE_MALFORMED)
        key = entry["record_id"]
        _refuse(not key or key in entries, cv.EXPORT_REPLAY_FILE_MALFORMED)
        entries[key] = entry
    return entries


def _run_identity(run_dir: Path, run: dict) -> dict:
    return {
        "candidates_sha256": hashlib.sha256(
            (run_dir / generate.CANDIDATES_FILENAME).read_bytes()
        ).hexdigest(),
        **{key: run[key] for key in ("seed", "produced_at", "harness_sha256")},
        "catalog": {key: run["catalog"][key] for key in ("catalog_id", "programs_sha256")},
    }


def load_replay(replay_dir: Path | None, run_dir: Path, run: dict) -> ReplayReport:
    if replay_dir is None:
        return ReplayReport()
    report = _read_report(Path(replay_dir) / replay.REPLAY_FILENAME)
    entries = _replay_entries(report)
    expected = _run_identity(run_dir, run)
    identity = report.get("run_identity")
    _refuse(not _shape(identity, {
        "candidates_sha256": str, "seed": int, "produced_at": str, "harness_sha256": str,
        "catalog": {"catalog_id": str, "programs_sha256": str},
    }), cv.EXPORT_REPLAY_RUN_IDENTITY_MISMATCH)
    _refuse(any(identity[key] != value for key, value in expected.items()),
            cv.EXPORT_REPLAY_RUN_IDENTITY_MISMATCH)
    return ReplayReport(report["status"], entries)


def bind_catalog(run: dict, pinned: catalog.Catalog) -> lineage.SplitPolicy | None:
    _refuse(not _shape(run, {"catalog": {"programs_sha256": str}}),
            cv.EXPORT_CATALOG_MISMATCH)
    _refuse(run["catalog"]["programs_sha256"] != pinned.programs_sha256,
            cv.EXPORT_CATALOG_MISMATCH)
    policy_json = run.get("split_policy")
    try:
        policy = None if policy_json is None else lineage.SplitPolicy.from_json(policy_json)
    except cv.RepairRefusal as exc:
        raise cv.RepairRefusal(cv.FINDING_EXPORT_INTEGRITY, cv.EXPORT_CATALOG_MISMATCH) from exc
    if pinned.split_policy is not None:
        _refuse(policy is None or policy.sha256 != pinned.split_policy.sha256,
                cv.EXPORT_CATALOG_MISMATCH)
    return policy


def check_lineages(records: list[dict], pinned: catalog.Catalog) -> None:
    programs = {p.program_id: p for p in pinned.programs}
    policy_digest = None if pinned.split_policy is None else pinned.split_policy.sha256
    for record in records:
        block = record["provenance"]["split_lineage"]
        program = programs.get(record["scenario"]["source"]["program_id"])
        _refuse(program is None, cv.EXPORT_SPLIT_REDERIVATION_MISMATCH)
        expected = {"lineage_id": program.program_id, "group_id": program.group_id,
                    "split": program.split, "policy_sha256": policy_digest}
        _refuse(any(block[key] != value for key, value in expected.items()),
                cv.EXPORT_SPLIT_REDERIVATION_MISMATCH)


def check_summary(run: dict, records: list[dict]) -> None:
    _refuse(type(run.get("records")) is not int or run["records"] != len(records),
            cv.EXPORT_RUN_SUMMARY_MISMATCH)
    for key, field in (("outcomes", "outcome"), ("oracle_statuses", "oracle_status")):
        observed = Counter(record["result"][field] for record in records)
        counts = run.get(key)
        _refuse(not isinstance(counts, dict), cv.EXPORT_RUN_SUMMARY_MISMATCH)
        _refuse(any(type(v) is not int or v < 0 for v in counts.values()),
                cv.EXPORT_RUN_SUMMARY_MISMATCH)
        _refuse(Counter(counts) != observed, cv.EXPORT_RUN_SUMMARY_MISMATCH)


bind_import_twin(__name__)
