"""Input bindings and family shapes checked before export projection or verdict derivation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog
from . import lineage
from . import replay
from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json

def _shape(value: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return _object_shape(value, expected)
    if isinstance(expected, list):
        return isinstance(value, list) and all(_shape(v, expected[0]) for v in value)
    if isinstance(expected, tuple):
        return any(_shape(value, choice) for choice in expected)
    return _exact(value, expected)


def _exact(value: Any, expected: type) -> bool:
    """``isinstance`` with one exception: a bool is never an int here."""

    if expected is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, expected)


def _object_shape(value: Any, fields: dict) -> bool:
    if not isinstance(value, dict):
        return False
    return all(key in value and _shape(value[key], shape) for key, shape in fields.items())


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
        report = load_strict_json(path.read_bytes())
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


def load_replay(replay_dir, run_dir, run, *, records, catalog, candidates_sha256) -> ReplayReport:
    if replay_dir is None:
        return ReplayReport()
    from . import trusted_replay
    from .run_validation import run_identity
    report = _read_report(Path(replay_dir) / replay.REPLAY_FILENAME)
    _replay_entries(report)
    expected = run_identity(run, candidates_sha256)
    _refuse(report.get("run_identity") != expected, cv.EXPORT_REPLAY_RUN_IDENTITY_MISMATCH)
    fresh = trusted_replay.replay_records(run, records, catalog=catalog,
                                          candidates_sha256=candidates_sha256)
    _refuse(any(report.get(key) != fresh[key] for key in
                ("status", "records", "counts", "catalog", "harness_sha256", "interpreter")),
            cv.EXPORT_REPLAY_RUN_IDENTITY_MISMATCH)
    return ReplayReport(fresh["status"], _replay_entries(fresh))


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


bind_import_twin(__name__)
