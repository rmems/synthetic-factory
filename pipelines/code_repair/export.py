#!/usr/bin/env python3
"""The export: evidence, SFT rows and the consumer's rows into a brand-new tree, with proof.

Every record is re-validated against the shared contract (envelope, digest,
label leak) and its verdict re-derived from its stored rows before anything is
written; an integrity failure on any record refuses the whole export because
the file's integrity is in question. Natural ineligibility (a rejected
outcome, an abstained oracle, a provisional status) never blocks: such records
stay in the evidence file and are counted per code. Positive rows are
deduplicated (exact broken text, canonical structure, a per-lineage cap),
proven to keep every lineage and group inside one split, re-bucketed with the
pinned policy, and written per split; the held-out split is frozen by digest.
``MANIFEST.json`` states the pipeline status, the replay status, the
admission blockers (dataset admission is S4, owner-gated), the evaluation
limitations (never blockers) and the prerequisites of the Agoge training run.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import catalog
from . import executor as ex
from . import generate
from . import lineage
from . import replay
from . import verify
from . import views
from . import vocabulary as cv
from ._contract import bind_import_twin, is_under_raw, oc, vocab

EXPORT_FORMAT = "code-repair-export/1"
MANIFEST_FILENAME = "MANIFEST.json"
EVIDENCE_PATH = "evidence/candidates.jsonl"
SFT_DIR = "sft"
AGOGE_PATH = "agoge/code_repair_v1.jsonl"
FREEZE_PATH = "held_out/FREEZE.json"
DEFAULT_LINEAGE_CAP = 6
DECISIONS_NEEDED = ("D-A", "D-B", "D-C", "D-D", "D-E")

__all__ = [
    "AGOGE_PATH", "DEFAULT_LINEAGE_CAP", "EVIDENCE_PATH", "EXPORT_FORMAT", "ExportRequest",
    "FREEZE_PATH", "MANIFEST_FILENAME", "SFT_DIR", "admission_blockers", "run",
]


@dataclass(frozen=True)
class ExportRequest:
    run_dir: Path
    out_dir: Path
    replay_dir: Path | None = None
    lineage_cap: int = DEFAULT_LINEAGE_CAP


@dataclass(frozen=True)
class Gates:
    """The factory's admission gates as the export sees them (S4 wires the real ones)."""

    registry_row_present: bool = False
    rights_allow_training: bool = False
    record_kind_routed: bool = False
    round_published: bool = False


@dataclass
class _Corpus:
    run: dict[str, Any]
    records: list[dict[str, Any]]
    policy: lineage.SplitPolicy | None
    replay_entries: dict[str, dict[str, Any]] | None
    positives: list[dict[str, Any]] = field(default_factory=list)
    rows: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    agoge_rows: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    dispositions: Counter = field(default_factory=Counter)
    per_lineage: Counter = field(default_factory=Counter)
    cap: int = DEFAULT_LINEAGE_CAP


# --- request and inputs ------------------------------------------------------------


def _check_request(request: ExportRequest) -> None:
    run_dir, out_dir = Path(request.run_dir), Path(request.out_dir)
    cv.refuse_first((
        (not (run_dir / generate.CANDIDATES_FILENAME).is_file(), cv.FINDING_RUN_FILE_MISSING,
         f"{run_dir / generate.CANDIDATES_FILENAME} is missing"),
        (not (run_dir / generate.RUN_FILENAME).is_file(), cv.FINDING_RUN_FILE_MISSING,
         f"{run_dir / generate.RUN_FILENAME} is missing"),
        (is_under_raw(out_dir), cv.FINDING_DESTINATION_UNDER_RAW,
         f"{out_dir} names or aliases the raw tree"),
        (out_dir.exists(), cv.FINDING_DESTINATION_EXISTS, f"{out_dir} already exists"),
        (not vocab.is_genuine_int(request.lineage_cap) or request.lineage_cap < 1,
         cv.FINDING_CAP_OUT_OF_DOMAIN, "lineage_cap must be a positive integer"),
    ))


def _load_run(run_dir: Path) -> dict[str, Any]:
    try:
        run = json.loads((run_dir / generate.RUN_FILENAME).read_text(encoding="utf-8"))
    except ValueError as exc:
        raise cv.RepairRefusal(cv.FINDING_RUN_FILE_MISSING, f"RUN.json is not JSON: {exc}") from exc
    cv.refuse_when(
        not isinstance(run, dict) or run.get("format") != generate.RUN_FORMAT,
        cv.FINDING_RUN_FILE_MISSING, "RUN.json is not a code-repair run summary",
    )
    return run


def _load_records(run_dir: Path) -> list[dict[str, Any]]:
    records = []
    for lineno, record in oc.iter_jsonl(run_dir / generate.CANDIDATES_FILENAME):
        cv.refuse_when(
            not isinstance(record, dict), cv.FINDING_RECORD_MALFORMED,
            f"{generate.CANDIDATES_FILENAME}:{lineno} is not a record",
        )
        records.append(record)
    return records


def _load_replay(replay_dir: Path | None) -> dict[str, dict[str, Any]] | None:
    if replay_dir is None:
        return None
    path = Path(replay_dir) / replay.REPLAY_FILENAME
    cv.refuse_when(not path.is_file(), cv.FINDING_REPLAY_FILE_MISSING, f"{path} is missing")
    report = json.loads(path.read_text(encoding="utf-8"))
    cv.refuse_when(
        report.get("format") != replay.REPLAY_FORMAT, cv.FINDING_REPLAY_FILE_MISSING,
        f"{path} is not a replay report",
    )
    return {entry["record_id"]: entry for entry in report.get("records", [])}


# --- integrity -----------------------------------------------------------------------


def _stored_phase(block: dict[str, Any] | None) -> ex.PhaseReport | None:
    if block is None:
        return None
    return ex.PhaseReport(
        block["status"], bool(block["load_ok"]), tuple(block["public"]), tuple(block["hidden"])
    )


def _rederived_verdict(record: dict[str, Any]) -> verify.Verdict:
    """The verdict the decision table gives the stored rows, with the stored context."""

    result, scenario = record["result"], record["scenario"]
    phases = verify.Phases(
        _stored_phase(result["phases"][cv.PHASE_ORIGINAL]),
        _stored_phase(result["phases"][cv.PHASE_MUTANT]),
        _stored_phase(result["phases"][cv.PHASE_REPAIRED]),
        _stored_phase(result["phases"].get(cv.PHASE_REFERENCE)),
    )
    hidden = record["oracle"]["configuration"]["hidden_check"]
    repaired = views.completion_of(record)
    function = scenario["source"]["upstream"]["function"]
    stored_examples = [(e["source"], e["want"]) for e in scenario["public_tests"]["examples"]]
    try:
        repaired_examples = [(e.source, e.want) for e in catalog.examples_of(repaired, function)]
    except (SyntaxError, ValueError):
        repaired_examples = None
    context = verify.DecisionContext(
        hidden["kind"], result["repaired_sha256"] == scenario["source"]["module_sha256"],
        repaired_examples != stored_examples, len(hidden["cases"]),
    )
    return verify.decide(phases, context)


def _integrity_failure(record: dict[str, Any], replay_entries: dict | None) -> str | None:
    """The integrity code that refuses the export, or None when the record is sound."""

    where = str(record.get("id", "record"))
    if oc.check_envelope(record, where) or oc.check_oracle_label_leak(record, where):
        return cv.EXPORT_RECORD_FAILS_CONTRACT
    if oc.check_digest(record, where):
        return cv.EXPORT_EVIDENCE_DIGEST_MISMATCH
    verdict = _rederived_verdict(record)
    result = record["result"]
    stored = (result["outcome"], list(result["reason_codes"]), result["oracle_status"])
    if (verdict.outcome, list(verdict.reason_codes), verdict.oracle_status) != stored:
        return cv.EXPORT_EVIDENCE_VERDICT_MISMATCH
    return _replay_failure(record, replay_entries)


def _replay_failure(record: dict[str, Any], replay_entries: dict | None) -> str | None:
    if replay_entries is None or not views.is_positive(record):
        return None
    entry = replay_entries.get(record["id"])
    if entry is None or entry.get("status") != "replayed":
        return cv.BLOCKER_REPLAY_NOT_RUN
    return None if entry.get("code") == cv.REPLAY_PASSED else entry["code"]


def _check_integrity(corpus: _Corpus) -> None:
    for record in corpus.records:
        code = _integrity_failure(record, corpus.replay_entries)
        cv.refuse_when(
            code is not None, cv.FINDING_EXPORT_INTEGRITY,
            f"record {record.get('id')} fails integrity ({code}); the run is not exportable",
        )


# --- positives, proofs, dedup ----------------------------------------------------------


def _lineage_of(record: dict[str, Any]) -> dict[str, Any]:
    return record["provenance"]["split_lineage"]


def _split_proof(corpus: _Corpus) -> None:
    """Every lineage and group sits in one split, and the pinned policy re-derives it."""

    by_lineage: dict[str, set[str]] = {}
    by_group: dict[str, set[str]] = {}
    for record in corpus.positives:
        lineage_block = _lineage_of(record)
        split = lineage_block.get("split")
        cv.refuse_when(
            split not in lineage.SPLITS, cv.FINDING_EXPORT_INTEGRITY,
            f"record {record['id']}: {cv.EXPORT_SPLIT_UNASSIGNED}",
        )
        by_lineage.setdefault(lineage_block["lineage_id"], set()).add(split)
        if lineage_block.get("group_id"):
            by_group.setdefault(lineage_block["group_id"], set()).add(split)
        _rederive_split(corpus, record, lineage_block)
    _refuse_crossing(by_lineage, cv.EXPORT_LINEAGE_CROSSES_SPLITS)
    _refuse_crossing(by_group, cv.EXPORT_GROUP_CROSSES_SPLITS)


def _refuse_crossing(by_key: dict[str, set[str]], code: str) -> None:
    crossing = sorted(key for key, splits in by_key.items() if len(splits) > 1)
    cv.refuse_when(bool(crossing), cv.FINDING_EXPORT_INTEGRITY, f"{code}: {', '.join(crossing)}")


def _rederive_split(corpus: _Corpus, record: dict[str, Any], block: dict[str, Any]) -> None:
    if corpus.policy is None:
        return
    policy_matches = block.get("policy_sha256") == corpus.policy.sha256
    anchor = lineage.anchor_for(block.get("group_id"), block["lineage_id"])
    expected = lineage.bucket_split(anchor, corpus.policy)
    cv.refuse_when(
        not policy_matches or expected != block["split"], cv.FINDING_EXPORT_INTEGRITY,
        f"record {record['id']}: {cv.EXPORT_SPLIT_REDERIVATION_MISMATCH}",
    )


def _duplicate_code(
    corpus: _Corpus, record: dict[str, Any], seen: dict[str, set[str]]
) -> str | None:
    broken = record["scenario"]["broken_program"]["files"][cv.PROGRAM_FILENAME]
    exact = record["result"]["broken_sha256"]
    structural = lineage.structure_digest(broken)
    lineage_id = _lineage_of(record)["lineage_id"]
    if exact in seen["exact"]:
        return cv.EXPORT_DUPLICATE_EXACT
    if structural in seen["structural"]:
        return cv.EXPORT_DUPLICATE_STRUCTURAL
    if corpus.per_lineage[lineage_id] >= corpus.cap:
        return cv.EXPORT_LINEAGE_CAP_APPLIED
    seen["exact"].add(exact)
    seen["structural"].add(structural)
    corpus.per_lineage[lineage_id] += 1
    return None


def _project(corpus: _Corpus) -> None:
    """Positive rows per split after dedup; every view is leak-checked before it is kept."""

    seen: dict[str, set[str]] = {"exact": set(), "structural": set()}
    for record in sorted(corpus.positives, key=lambda r: r["id"]):
        code = _duplicate_code(corpus, record, seen)
        if code is not None:
            corpus.dispositions[code] += 1
            continue
        row = views.sft_row(record)
        leaks = views.view_findings(record, row)
        cv.refuse_when(
            bool(leaks), cv.FINDING_EXPORT_INTEGRITY, f"record {record['id']} leaks: {leaks}"
        )
        split = _lineage_of(record)["split"]
        corpus.rows.setdefault(split, []).append(row)
        corpus.agoge_rows.setdefault(split, []).append(views.agoge_row(record))
        corpus.dispositions["exported"] += 1


# --- admission -----------------------------------------------------------------------------


def admission_blockers(gates: Gates, *, replay_passed: bool, exported_rows: int) -> list[str]:
    """Dataset-admission blockers only; evaluation limitations are never among them."""

    blockers = []
    if not gates.registry_row_present:
        blockers.append(cv.BLOCKER_REGISTRY_ROW_MISSING)
    if not gates.rights_allow_training:
        blockers.append(cv.BLOCKER_RIGHTS_PROFILE_MISSING)
    if not gates.record_kind_routed:
        blockers.append(cv.BLOCKER_RECORD_KIND_UNSUPPORTED)
    if not replay_passed:
        blockers.append(cv.BLOCKER_REPLAY_NOT_RUN)
    if exported_rows == 0:
        blockers.append(cv.BLOCKER_NO_VALIDATED_ACCEPTED_ROWS)
    if not gates.round_published:
        blockers.append(cv.BLOCKER_ROUND_NOT_PUBLISHED)
    return blockers


# --- manifest and writing ----------------------------------------------------------------------


def _tables(corpus: _Corpus) -> dict[str, Any]:
    outcomes = Counter(r["result"]["outcome"] for r in corpus.records)
    statuses = Counter(r["result"]["oracle_status"] for r in corpus.records)
    reasons = Counter(code for r in corpus.records for code in r["result"]["reason_codes"])
    families = Counter(r["scenario"]["source"]["family"] for r in corpus.positives)
    operators = Counter(r["intervention"]["operator"] for r in corpus.positives)
    return {
        "records": len(corpus.records), "outcomes": dict(sorted(outcomes.items())),
        "oracle_statuses": dict(sorted(statuses.items())),
        "reasons": dict(sorted(reasons.items())),
        "positives": len(corpus.positives),
        "dispositions": dict(sorted(corpus.dispositions.items())),
        "per_split": {s: len(rows) for s, rows in sorted(corpus.rows.items())},
        "per_family_positives": dict(sorted(families.items())),
        "per_operator_positives": dict(sorted(operators.items())),
        "per_lineage_exported": dict(sorted(corpus.per_lineage.items())),
        "independent_lineages_exported": len(corpus.per_lineage),
    }


def _write_jsonl(root: Path, relative: str, rows: list[dict[str, Any]]) -> None:
    oc.write_jsonl(root / relative, rows)


def _write_json(root: Path, relative: str, payload: dict[str, Any]) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _digests(root: Path, relatives: list[str]) -> dict[str, str]:
    return {r: hashlib.sha256((root / r).read_bytes()).hexdigest() for r in relatives}


def _write(request: ExportRequest, corpus: _Corpus) -> dict[str, Any]:
    root = Path(request.out_dir)
    root.mkdir(parents=True, exist_ok=False)
    written = [EVIDENCE_PATH, AGOGE_PATH]
    _write_jsonl(root, EVIDENCE_PATH, corpus.records)
    for split in lineage.SPLITS:
        _write_jsonl(root, f"{SFT_DIR}/{split}.jsonl", corpus.rows.get(split, []))
        written.append(f"{SFT_DIR}/{split}.jsonl")
    agoge = [row for split in lineage.SPLITS for row in corpus.agoge_rows.get(split, [])]
    _write_jsonl(root, AGOGE_PATH, agoge)
    held = corpus.agoge_rows.get("held_out", [])
    _write_json(root, FREEZE_PATH, {
        "format": EXPORT_FORMAT, "split": "held_out",
        "canonical_ids": [row["canonical_id"] for row in held],
        "sft_sha256": _digests(root, [f"{SFT_DIR}/held_out.jsonl"])[f"{SFT_DIR}/held_out.jsonl"],
        "policy_sha256": None if corpus.policy is None else corpus.policy.sha256,
    })
    written.append(FREEZE_PATH)
    manifest = _manifest(request, corpus, _digests(root, written))
    _write_json(root, MANIFEST_FILENAME, manifest)
    return manifest


def _manifest(request: ExportRequest, corpus: _Corpus, digests: dict[str, str]) -> dict[str, Any]:
    run = corpus.run
    replay_status = "not run" if corpus.replay_entries is None else "passed"
    tables = _tables(corpus)
    exported = tables["dispositions"].get("exported", 0)
    blockers = admission_blockers(
        Gates(), replay_passed=replay_status == "passed", exported_rows=exported
    )
    return {
        "format": EXPORT_FORMAT, "family": cv.FAMILY, "pipeline_status": "complete",
        "run": {k: run.get(k) for k in ("seed", "count", "produced_at", "catalog", "generator",
                                        "harness_sha256", "split_policy", "timeout_s")},
        "lineage_cap": request.lineage_cap, "tables": tables, "files": digests,
        "replay": replay_status,
        "admission": {
            "training_export": "blocked", "blockers": blockers,
            "decisions_needed": list(DECISIONS_NEEDED),
        },
        "evaluation_limitations": list(cv.LIMITATION_CODES),
        "training_run_prerequisites": list(cv.PREREQUISITE_CODES),
        "rights": {
            "upstream_license": run.get("catalog", {}).get("license", "MIT"),
            "attribution": "LICENSE.upstream in the catalog; NOTICE line pending (S4)",
            "project_training_policy": "blocked (no reviewed profile; issue D-B/D-C)",
        },
        "pretraining_exposure": "unknown",
    }


def run(request: ExportRequest) -> dict[str, Any]:
    """Export a run into a brand-new tree; returns the manifest."""

    _check_request(request)
    run_dir = Path(request.run_dir)
    run_meta = _load_run(run_dir)
    policy_json = run_meta.get("split_policy")
    corpus = _Corpus(
        run_meta, _load_records(run_dir),
        None if policy_json is None else lineage.SplitPolicy.from_json(policy_json),
        _load_replay(request.replay_dir), cap=request.lineage_cap,
    )
    _check_integrity(corpus)
    corpus.positives = [r for r in corpus.records if views.is_positive(r)]
    _split_proof(corpus)
    _project(corpus)
    return _write(request, corpus)


bind_import_twin(__name__)
