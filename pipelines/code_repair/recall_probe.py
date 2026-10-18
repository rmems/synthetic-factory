"""The offline recall probe: prompts out, completions scored, no model called here.

Every repair target is verbatim TheAlgorithms/Python code that code models
may have seen in pretraining, which the export records as the evaluation
limitation ``POSSIBLE_UPSTREAM_CODE_RECALL``: a model may recall the upstream
module rather than repair the broken one. The probe looks for that in two
steps the repository runs without a model. ``emit`` writes the two prompt
variants of :mod:`.recall_prompts` for every positive record of a run into a
brand-new directory. ``score`` reads completions produced elsewhere, binds the
prompts back to the run byte for byte, scores each completion with
:mod:`.recall_score` (hashed and parsed, never executed) and writes the report
to a brand-new file. An exact match under ``docstring_only`` is a recall
signal and an upper bound on contamination risk, not proof of memorisation:
the prompt still carries the function's specification, from which a short
function can be rebuilt verbatim.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import generate, lineage, recall_prompts, recall_score, views
from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, is_under_raw, oc
from .candidate_io import load_candidate_records

PROMPTS_FILENAME = "prompts.jsonl"
REPORT_FORMAT = "code-repair-recall-probe/1"
COMPLETION_KEYS = frozenset({"id", "variant", "completion"})
SCORING = (
    "exact: the SHA-256 of the completion text equals result.repaired_sha256; structural: the "
    "canonical AST digest of the completion equals the repaired module's; rates are over the "
    "completions received; no completion was executed"
)

__all__ = [
    "COMPLETION_KEYS", "PROMPTS_FILENAME", "REPORT_FORMAT", "SCORING", "EmitRequest",
    "ScoreRequest", "emit", "score",
]

Key = tuple[str, str]


# --- the run and the destinations -------------------------------------------------------------


@dataclass(frozen=True)
class _Run:
    candidates_sha256: str
    records: list[dict[str, Any]]
    rows: list[dict[str, Any]]

    @property
    def positives(self) -> int:
        return len(self.rows) // len(cv.RECALL_VARIANTS)

    def as_json(self) -> dict[str, Any]:
        return {
            "candidates_sha256": self.candidates_sha256, "records": len(self.records),
            "positives": self.positives,
        }

    def targets(self) -> dict[str, recall_score.Target]:
        ids = {row["id"] for row in self.rows}
        return {record["id"]: _target(record) for record in self.records
                if record.get("id") in ids}


def _target(record: dict[str, Any]) -> recall_score.Target:
    return recall_score.Target(
        record["result"]["repaired_sha256"],
        lineage.structure_digest(views.completion_of(record)),
        record["scenario"]["source"]["family"],
    )


def _prompt_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    positives = [record for record in records if views.is_positive(record)]
    return [row for record in positives for row in recall_prompts.prompt_rows(record)]


def _load_run(run_dir: Path) -> _Run:
    path = Path(run_dir) / generate.CANDIDATES_FILENAME
    cv.refuse_when(not path.is_file(), cv.FINDING_RUN_FILE_MISSING, f"{cv.shown(path)} is missing")
    data = path.read_bytes()
    records = load_candidate_records(data)
    rows = _prompt_rows(records)
    cv.refuse_when(
        not rows, cv.FINDING_RECALL_NO_POSITIVE_RECORDS,
        "the run has no accepted, validated, eligible record to probe",
    )
    return _Run(hashlib.sha256(data).hexdigest(), records, rows)


def _exists(destination: Path) -> cv.RepairRefusal:
    return cv.RepairRefusal(cv.FINDING_DESTINATION_EXISTS,
                            f"{cv.shown(str(destination))} already exists")


def _check_destination(destination: Path) -> None:
    cv.refuse_when(is_under_raw(destination), cv.FINDING_DESTINATION_UNDER_RAW,
                   f"{cv.shown(str(destination))} names or aliases the raw tree")
    if destination.exists():
        raise _exists(destination)


def _make_directory(out_dir: Path) -> None:
    """Created here or refused: a directory that appeared after the check is never reused."""

    try:
        out_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise _exists(out_dir) from exc


def _file_entry(path: Path, data: bytes, rows: int) -> dict[str, Any]:
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "rows": rows}


# --- emit -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class EmitRequest:
    run_dir: Path
    out_dir: Path


def emit(request: EmitRequest) -> dict[str, Any]:
    """Write ``prompts.jsonl`` for every positive record into a brand-new directory."""

    out_dir = Path(request.out_dir)
    _check_destination(out_dir)
    run = _load_run(request.run_dir)
    _make_directory(out_dir)
    prompts = out_dir / PROMPTS_FILENAME
    oc.write_jsonl(prompts, run.rows)
    return {
        "format": REPORT_FORMAT, "command": "emit", "family": cv.FAMILY,
        "limitation": cv.LIMITATION_POSSIBLE_UPSTREAM_CODE_RECALL, "run": run.as_json(),
        "prompts": _file_entry(prompts, prompts.read_bytes(), len(run.rows)),
        "per_variant": dict(sorted(Counter(row["variant"] for row in run.rows).items())),
    }


# --- score inputs -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoreRequest:
    prompts_path: Path
    completions_path: Path
    run_dir: Path
    out_path: Path


@dataclass(frozen=True)
class _Input:
    """One input file, read once: its bytes are what is hashed and what is parsed."""

    path: Path
    data: bytes

    @classmethod
    def read(cls, path: Path, what: str) -> _Input:
        path = Path(path)
        cv.refuse_when(not path.is_file(), cv.FINDING_RECALL_INPUT_MISSING,
                       f"{what} file {cv.shown(str(path))} is missing")
        return cls(path, path.read_bytes())

    def lines(self):
        return oc.iter_jsonl_bytes(self.data)

    def entry(self, rows: int) -> dict[str, Any]:
        return _file_entry(self.path, self.data, rows)


def _is_keyed(row: Any) -> bool:
    """A parsed line that is an object whose ``id`` and ``variant`` are both strings."""

    if not isinstance(row, dict):
        return False
    return isinstance(row.get("id"), str) and isinstance(row.get("variant"), str)


def _key_of(row: dict[str, Any]) -> Key:
    """``(id, variant)`` of a row :func:`_is_keyed` accepted."""

    return row["id"], row["variant"]


def _prompt_key(row: Any, expected: dict[Key, dict[str, Any]], where: str) -> Key:
    """The key of a prompt row the run re-renders byte for byte; refused otherwise."""

    cv.refuse_when(not _is_keyed(row), cv.FINDING_RECALL_PROMPTS_MALFORMED,
                   f"{where} is not a prompt row with string id and variant")
    key = _key_of(row)
    cv.refuse_when(expected.get(key) != row, cv.FINDING_RECALL_PROMPTS_MALFORMED,
                   f"{where} is not a prompt the run re-renders")
    return key


def _bind_prompts(prompts: _Input, run: _Run) -> dict[Key, dict[str, Any]]:
    """Every prompt row must be one the run re-renders byte for byte, once, and all of them."""

    expected = {(row["id"], row["variant"]): row for row in run.rows}
    seen: dict[Key, dict[str, Any]] = {}
    for lineno, row in prompts.lines():
        where = f"{prompts.path.name}:{lineno}"
        key = _prompt_key(row, expected, where)
        cv.refuse_when(key in seen, cv.FINDING_RECALL_PROMPTS_MALFORMED, f"{where} repeats a prompt")
        seen[key] = row
    cv.refuse_when(
        set(seen) != set(expected), cv.FINDING_RECALL_PROMPTS_MALFORMED,
        f"{prompts.path.name} does not carry both variants of every positive record of the run",
    )
    return seen


def _is_completion_row(row: Any) -> bool:
    if not isinstance(row, dict) or set(row) != COMPLETION_KEYS:
        return False
    return all(isinstance(value, str) for value in row.values())


def _completion(row: Any, prompts: dict[Key, dict[str, Any]], where: str) -> tuple[Key, str]:
    """``((id, variant), completion)`` of one well-formed line naming an emitted prompt."""

    if not _is_completion_row(row):
        raise cv.RepairRefusal(
            cv.FINDING_RECALL_COMPLETION_MALFORMED,
            f"{where} is not an object with exactly the string fields {sorted(COMPLETION_KEYS)}",
        )
    key = _key_of(row)
    cv.refuse_when(
        key not in prompts, cv.FINDING_RECALL_COMPLETION_UNKNOWN,
        f"{where} names no emitted prompt: id {cv.shown(key[0])} variant {cv.shown(key[1])}",
    )
    return key, row["completion"]


def _read_completions(completions: _Input, prompts: dict[Key, dict[str, Any]]) -> dict[Key, str]:
    found: dict[Key, str] = {}
    for lineno, row in completions.lines():
        where = f"{completions.path.name}:{lineno}"
        key, completion = _completion(row, prompts, where)
        cv.refuse_when(key in found, cv.FINDING_RECALL_COMPLETION_DUPLICATE,
                       f"{where} repeats id {cv.shown(key[0])} variant {key[1]}")
        found[key] = completion
    cv.refuse_when(not found, cv.FINDING_RECALL_INPUT_MISSING,
                   f"completions file {cv.shown(str(completions.path))} carries no completion row")
    return found


# --- score ------------------------------------------------------------------------------------


def _write_report(path: Path, report: dict[str, Any]) -> None:
    """Created here or refused: a file that appeared after the check is never overwritten."""

    text = dumps_exact_json(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text)
    except FileExistsError as exc:
        raise _exists(path) from exc


def _findings(counted: recall_score.Tally, prompts: dict[Key, dict[str, Any]]) -> list[dict]:
    return [
        {"code": cv.RECALL_EXACT_UNDER_DOCSTRING_ONLY, "record_id": record_id,
         "family": prompts[(record_id, cv.RECALL_VARIANT_DOCSTRING_ONLY)]["family"]}
        for record_id in sorted(counted.recalled)
    ]


def score(request: ScoreRequest) -> dict[str, Any]:
    """Score completions produced elsewhere against the run's verified repairs; write the report
    to a brand-new file and return it. No completion is executed."""

    out_path = Path(request.out_path)
    _check_destination(out_path)
    run = _load_run(request.run_dir)
    prompts_input = _Input.read(request.prompts_path, "prompts")
    prompts = _bind_prompts(prompts_input, run)
    completions_input = _Input.read(request.completions_path, "completions")
    completions = _read_completions(completions_input, prompts)
    counted = recall_score.tally(prompts, completions, run.targets())
    findings = _findings(counted, prompts)
    report = {
        "format": REPORT_FORMAT, "command": "score", "family": cv.FAMILY,
        "limitation": cv.LIMITATION_POSSIBLE_UPSTREAM_CODE_RECALL, "scoring": SCORING,
        "run": run.as_json(),
        "inputs": {
            "prompts": prompts_input.entry(len(prompts)),
            "completions": completions_input.entry(len(completions)),
        },
        **counted.as_json(),
        "findings": findings, "status": "findings" if findings else "ok",
    }
    _write_report(out_path, report)
    return report


bind_import_twin(__name__)
