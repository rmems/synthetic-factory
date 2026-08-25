#!/usr/bin/env python3
"""Integration and promotion gate for the curation pass (bead ``sf-c5l.7``).

The six curation lanes each write their own curated JSONL tree plus a
record-level manifest. This module is the seventh, final step: it composes
those lane outputs into **one brand-new cleaned destination**, runs every
structural and corpus-level gate on that destination, records a stratified
human-review sample, and promotes to a **brand-new curated path** only when
``training_ready`` is true and the sample has been reviewed.

Composition order
-----------------

The order is data, not code: it lives in an integration plan (``--plan``) so a
reviewer can read the exact chain that produced a corpus. Lane outputs are
overlaid onto the destination in plan order, so a later transform in the chain
supersedes an earlier one for any relative path both emit. Every supersession is
recorded in the manifest -- nothing is silently overwritten.

The documented order for run ``2026-08-17`` is::

    1. sf-c5l.1  bridge_event_time_order   (timing repair / quarantine)
    2. sf-c5l.2  curate_identity           (canonical IDs + provenance)
    3. sf-c5l.3  preference_purity         (same-context pairs)
    4. sf-c5l.4  reward_ontology           (comparability classes)
    5. sf-c5l.5  coding_observability      (no hidden chain-of-thought)
    6. sf-c5l.6  tag_taxonomy              (controlled vocabulary)

Plan schema (``curation-integration-plan/v1``)::

    {
      "schema": "curation-integration-plan/v1",
      "source_run": "outputs/raw/2026-08-17",
      "lanes": [
        {
          "bead": "sf-c5l.1",
          "transform": "bridge_event_time_order",
          "version": "1.0.0",
          "outputs": "lane-bridge",              # dir of curated *.jsonl
          "manifest": "lane-bridge/manifest.jsonl"   # optional, record-level
        }
      ]
    }

Relative ``outputs``/``manifest`` paths resolve against the plan file's
directory.

Usage
-----

::

    python3 pipelines/curate_gate.py integrate \\
        --plan outputs/curation/plan.json \\
        --cleaned-out outputs/cleaned/2026-08-17-curated-v1

    # a human fills in verdicts for every sampled record, then:
    python3 pipelines/curate_gate.py promote \\
        --cleaned outputs/cleaned/2026-08-17-curated-v1 \\
        --review review-verdicts.json \\
        --curated-out outputs/curated/2026-08-17-v1

Both subcommands refuse to write into a destination that already exists, and
neither ever writes into ``outputs/raw/``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

_PIPELINES = Path(__file__).resolve().parent
_REPO = _PIPELINES.parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import promote as promote_module  # noqa: E402
import training_audit  # noqa: E402
from check_records import canonical_record_id, reject_json_constant  # noqa: E402
from validate_run import check_line  # noqa: E402

TOOL_NAME = "curate_gate"
TOOL_VERSION = "1.0.0"

PLAN_SCHEMA = "curation-integration-plan/v1"
MANIFEST_SCHEMA = "curation-manifest/v1"
SAMPLE_SCHEMA = "curation-review-sample/v1"
REVIEW_SCHEMA = "curation-review-verdicts/v1"

MANIFEST_FILENAME = "curation-manifest.json"
SAMPLE_FILENAME = "review-sample.json"
REVIEW_FILENAME = "review-verdicts.json"

VALIDATOR = _PIPELINES / "validate_run.py"
CHECKER = _PIPELINES / "check_records.py"

DEFAULT_PER_STRATUM = 2

RAW_OUTPUT_ROOT = (_REPO / "outputs" / "raw").resolve()

# The integration gate is meaningful only after every upstream lane has run.
# Bead IDs fix the dependency order; transform names bind each position to the
# reviewed implementation contract rather than accepting an arbitrary subset.
REQUIRED_LANES = (
    ("sf-c5l.1", "bridge_event_time_order"),
    ("sf-c5l.2", "curate_identity"),
    ("sf-c5l.3", "same-context-preference-curation"),
    ("sf-c5l.4", "reward_ontology"),
    ("sf-c5l.5", "coding_observability"),
    ("sf-c5l.6", "tag_taxonomy"),
)

# Which Thalamic view speaks for a record when stratifying by safety gate.
DECISION_ROLE_PRIORITY = ("record", "chosen", "language_view.trajectory", "rejected")

EXCLUSION_ACTIONS = frozenset({"excluded", "exclude", "dropped", "drop"})
QUARANTINE_ACTIONS = frozenset({"quarantine", "quarantined"})

ACCEPT_VERDICTS = frozenset({"accept", "accepted", "pass"})
REJECT_VERDICTS = frozenset({"reject", "rejected", "fail", "block"})

MANIFEST_LIST_KEYS = ("decisions", "manifest", "entries", "records", "items")


class GateError(Exception):
    """Operator-facing failure: bad plan, bad input, or an unsafe destination."""


# ---------------------------------------------------------------------------
# hashing helpers
# ---------------------------------------------------------------------------


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonl_paths(root: Path) -> list[Path]:
    """Every ``*.jsonl`` under ``root``, ordered by relative path."""
    return sorted(root.rglob("*.jsonl"), key=lambda path: path.relative_to(root).parts)


def count_records(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    return sum(1 for line in text.splitlines() if line.strip())


def corpus_digest(root: Path) -> str:
    """Digest of the JSONL corpus only, so sidecar reports do not disturb it."""
    digest = hashlib.sha256()
    for path in jsonl_paths(root):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return f"sha256:{digest.hexdigest()}"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GateError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text, parse_constant=reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise GateError(f"{path}: invalid JSON: {exc}") from exc


def _resolve_declared_path(base: Path, value: str, label: str) -> Path:
    """Resolve one plan-relative path without erasing symlink evidence."""
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise GateError(f"{label} must stay within the plan directory: {value!r}")

    walked = base
    for part in declared.parts:
        if part in {"", "."}:
            continue
        walked = walked / part
        if walked.is_symlink():
            raise GateError(f"{label} contains a symlinked path component: {walked}")

    resolved = (base / declared).resolve()
    if resolved != base and base not in resolved.parents:
        raise GateError(f"{label} resolves outside the plan directory: {resolved}")
    return resolved


# ---------------------------------------------------------------------------
# integration plan
# ---------------------------------------------------------------------------


def load_plan(plan_path: Path) -> dict[str, Any]:
    """Read and validate an integration plan; resolve its lane paths."""
    plan_path = Path(plan_path).resolve()
    plan = _load_json(plan_path)
    if not isinstance(plan, dict):
        raise GateError(f"{plan_path}: plan must be a JSON object")
    schema = plan.get("schema")
    if schema is not None and schema != PLAN_SCHEMA:
        raise GateError(f"{plan_path}: unsupported plan schema {schema!r}")
    lanes = plan.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        raise GateError(f"{plan_path}: plan needs a non-empty 'lanes' list")

    base = plan_path.parent
    resolved: list[dict[str, Any]] = []
    versions: dict[str, str] = {}
    seen_outputs: dict[Path, str] = {}
    for index, lane in enumerate(lanes, 1):
        if not isinstance(lane, dict):
            raise GateError(f"{plan_path}: lane {index} must be an object")
        transform = lane.get("transform")
        version = lane.get("version")
        outputs = lane.get("outputs")
        for field, value in (("transform", transform), ("version", version), ("outputs", outputs)):
            if not isinstance(value, str) or not value.strip():
                raise GateError(f"{plan_path}: lane {index} needs a non-empty string '{field}'")
        previous = versions.get(transform)
        if previous is not None and previous != version:
            raise GateError(
                f"{plan_path}: transform {transform!r} declared at two versions "
                f"({previous!r} and {version!r})"
            )
        versions[transform] = version

        outputs_path = _resolve_declared_path(
            base, outputs, f"{plan_path}: lane {index} ({transform}) outputs"
        )
        if not outputs_path.is_dir():
            raise GateError(
                f"{plan_path}: lane {index} ({transform}) outputs directory is missing: "
                f"{outputs_path}"
            )
        if outputs_path in seen_outputs:
            raise GateError(
                f"{plan_path}: lane {index} ({transform}) reuses the outputs directory of "
                f"lane {seen_outputs[outputs_path]}: {outputs_path}"
            )
        seen_outputs[outputs_path] = f"{index} ({transform})"

        manifest = lane.get("manifest")
        manifest_path = None
        if manifest is not None:
            if not isinstance(manifest, str) or not manifest.strip():
                raise GateError(f"{plan_path}: lane {index} 'manifest' must be a non-empty string")
            manifest_path = _resolve_declared_path(
                base, manifest, f"{plan_path}: lane {index} ({transform}) manifest"
            )
            if not manifest_path.is_file():
                raise GateError(
                    f"{plan_path}: lane {index} ({transform}) manifest is missing: {manifest_path}"
                )

        resolved.append(
            {
                "order": index,
                "bead": lane.get("bead"),
                "transform": transform,
                "version": version,
                "outputs_dir": outputs_path,
                "manifest_path": manifest_path,
            }
        )

    declared_lanes = tuple((lane["bead"], lane["transform"]) for lane in resolved)
    if declared_lanes != REQUIRED_LANES:
        expected = ", ".join(f"{bead}:{transform}" for bead, transform in REQUIRED_LANES)
        actual = ", ".join(f"{bead}:{transform}" for bead, transform in declared_lanes)
        raise GateError(
            f"{plan_path}: lanes must be the six required contracts in order; "
            f"expected [{expected}], got [{actual}]"
        )

    return {
        "plan_path": plan_path,
        "plan_sha256": file_sha256(plan_path),
        "source_run": plan.get("source_run"),
        "lanes": resolved,
        "transform_versions": dict(sorted(versions.items())),
    }


# ---------------------------------------------------------------------------
# composition
# ---------------------------------------------------------------------------


def _assert_new_destination(destination: Path, label: str) -> None:
    destination = Path(destination).resolve(strict=False)
    if destination == RAW_OUTPUT_ROOT or RAW_OUTPUT_ROOT in destination.parents:
        raise GateError(f"refusing to write {label} beneath immutable raw output: {destination}")
    if destination.exists():
        raise GateError(f"refusing to overwrite an existing {label}: {destination}")


def compose(
    plan: dict[str, Any],
    destination: Path,
    *,
    logical_destination: Path | None = None,
) -> dict[str, Any]:
    """Overlay lane outputs into a brand-new ``destination`` in plan order."""
    destination = Path(destination).resolve()
    logical_destination = Path(logical_destination or destination).resolve()
    _assert_new_destination(destination, "cleaned destination")

    for lane in plan["lanes"]:
        outputs_dir = lane["outputs_dir"]
        if outputs_dir == logical_destination or logical_destination in outputs_dir.parents:
            raise GateError(
                f"lane {lane['order']} ({lane['transform']}) outputs live inside the "
                f"cleaned destination: {outputs_dir}"
            )
        if outputs_dir in logical_destination.parents:
            raise GateError(
                f"cleaned destination is nested inside lane {lane['order']} "
                f"({lane['transform']}) outputs: {outputs_dir}"
            )

    # Resolve every lane's payload before creating anything, so a bad plan
    # never leaves a half-built destination behind.
    lane_paths: list[tuple[dict[str, Any], list[Path]]] = []
    for lane in plan["lanes"]:
        outputs_dir = lane["outputs_dir"]
        paths = jsonl_paths(outputs_dir)
        # A lane may keep its record-level manifest inside its own output tree.
        # The manifest is provenance, not corpus, so it never joins the corpus.
        manifest_path = lane["manifest_path"]
        if manifest_path is not None:
            paths = [path for path in paths if path != manifest_path]
        if not paths:
            raise GateError(
                f"lane {lane['order']} ({lane['transform']}) contributed no *.jsonl: "
                f"{outputs_dir}"
            )
        for path in paths:
            # A symlinked lane output would silently pull bytes from outside the
            # declared tree into the curated corpus.
            walked = outputs_dir
            for part in path.relative_to(outputs_dir).parts:
                walked = walked / part
                if walked.is_symlink():
                    raise GateError(
                        f"lane {lane['order']} ({lane['transform']}) contains a "
                        f"symlinked path: {walked}"
                    )
        if sum(count_records(path) for path in paths) == 0:
            raise GateError(
                f"lane {lane['order']} ({lane['transform']}) contributed zero records: "
                f"{outputs_dir}"
            )
        lane_paths.append((lane, paths))

    try:
        destination.mkdir(parents=True)
    except FileExistsError as exc:
        raise GateError(
            f"refusing to overwrite an existing cleaned destination: {destination}"
        ) from exc
    owner: dict[str, dict[str, Any]] = {}
    supersessions: list[dict[str, Any]] = []
    inputs: list[dict[str, Any]] = []
    lane_summaries: list[dict[str, Any]] = []

    for lane, paths in lane_paths:
        outputs_dir = lane["outputs_dir"]
        lane_records = 0
        for source in paths:
            rel = source.relative_to(outputs_dir).as_posix()
            digest = file_sha256(source)
            records = count_records(source)
            lane_records += records
            inputs.append(
                {
                    "lane_order": lane["order"],
                    "transform": lane["transform"],
                    "path": rel,
                    "sha256": digest,
                    "bytes": source.stat().st_size,
                    "records": records,
                }
            )
            previous = owner.get(rel)
            if previous is not None:
                supersessions.append(
                    {
                        "path": rel,
                        "superseded_transform": previous["transform"],
                        "superseded_order": previous["lane_order"],
                        "superseded_sha256": previous["sha256"],
                        "winning_transform": lane["transform"],
                        "winning_order": lane["order"],
                        "winning_sha256": digest,
                    }
                )
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            owner[rel] = {
                "lane_order": lane["order"],
                "transform": lane["transform"],
                "version": lane["version"],
                "sha256": digest,
                "records": records,
            }
        lane_summaries.append(
            {
                "order": lane["order"],
                "bead": lane["bead"],
                "transform": lane["transform"],
                "version": lane["version"],
                "outputs": str(outputs_dir),
                "files": len(paths),
                "records": lane_records,
            }
        )

    outputs = []
    for rel in sorted(owner):
        entry = owner[rel]
        outputs.append(
            {
                "path": rel,
                "sha256": entry["sha256"],
                "bytes": (destination / rel).stat().st_size,
                "records": entry["records"],
                "transform": entry["transform"],
                "version": entry["version"],
                "lane_order": entry["lane_order"],
            }
        )

    return {
        "destination": logical_destination,
        "composition_order": lane_summaries,
        "inputs": inputs,
        "outputs": outputs,
        "supersessions": supersessions,
    }


# ---------------------------------------------------------------------------
# lane manifests: exclusions, quarantines, action counts
# ---------------------------------------------------------------------------


def _manifest_entries(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        entries = []
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line, parse_constant=reject_json_constant)
            except (json.JSONDecodeError, ValueError) as exc:
                raise GateError(f"{path}:{number}: invalid JSON manifest line: {exc}") from exc
            if not isinstance(entry, dict):
                raise GateError(f"{path}:{number}: manifest entry must be an object")
            entries.append(entry)
        return entries

    payload = _load_json(path)
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        candidates = None
        for key in MANIFEST_LIST_KEYS:
            value = payload.get(key)
            if isinstance(value, list):
                candidates = value
                break
        if candidates is None:
            raise GateError(
                f"{path}: manifest object needs one of {', '.join(MANIFEST_LIST_KEYS)} as a list"
            )
    else:
        raise GateError(f"{path}: manifest must be a list or an object")
    for entry in candidates:
        if not isinstance(entry, dict):
            raise GateError(f"{path}: every manifest entry must be an object")
    return list(candidates)


def _normalize_entry(entry: dict[str, Any], lane: dict[str, Any]) -> dict[str, Any]:
    reasons = entry.get("reason_codes")
    if isinstance(reasons, str):
        reasons = [reasons]
    elif not isinstance(reasons, list):
        reasons = []
    return {
        "lane_order": lane["order"],
        "transform": entry.get("transform_name") or lane["transform"],
        "version": entry.get("transform_version") or lane["version"],
        "action": entry.get("action"),
        "reason_codes": [str(reason) for reason in reasons],
        "source_path": entry.get("source_path"),
        "source_line": entry.get("source_line"),
        "source_hash": entry.get("source_hash"),
        "output_id": entry.get("output_id"),
        "output_hash": entry.get("output_hash"),
    }


def collect_lane_manifests(plan: dict[str, Any]) -> dict[str, Any]:
    """Fold every lane's record-level manifest into exclusions and counts."""
    exclusions: list[dict[str, Any]] = []
    quarantines: list[dict[str, Any]] = []
    actions_by_lane: dict[str, dict[str, int]] = {}
    reason_counts: Counter[str] = Counter()
    missing: list[str] = []

    for lane in plan["lanes"]:
        manifest_path = lane["manifest_path"]
        if manifest_path is None:
            missing.append(lane["transform"])
            continue
        counts: Counter[str] = Counter()
        for entry in _manifest_entries(manifest_path):
            normalized = _normalize_entry(entry, lane)
            action = normalized["action"]
            key = str(action) if action is not None else "unspecified"
            counts[key] += 1
            lowered = key.strip().lower()
            if lowered in EXCLUSION_ACTIONS:
                exclusions.append(normalized)
                reason_counts.update(normalized["reason_codes"] or ["UNSPECIFIED"])
            elif lowered in QUARANTINE_ACTIONS:
                quarantines.append(normalized)
                reason_counts.update(normalized["reason_codes"] or ["UNSPECIFIED"])
        actions_by_lane[lane["transform"]] = dict(sorted(counts.items()))

    return {
        "actions_by_lane": actions_by_lane,
        "lanes_without_manifest": missing,
        "exclusions": exclusions,
        "quarantines": quarantines,
        "reason_codes": dict(sorted(reason_counts.items())),
    }


# ---------------------------------------------------------------------------
# stratified review sample
# ---------------------------------------------------------------------------


def _primary_decision(obj: Any, kind: str) -> str:
    if not isinstance(obj, dict):
        return "none"
    decisions: dict[str, str] = {}
    for role, view in training_audit.thalamic_views(obj, kind):
        decision = training_audit.dict_field(view, "safety_decision").get("decision")
        if isinstance(decision, str) and decision.strip():
            decisions[role] = decision.strip()
    for role in DECISION_ROLE_PRIORITY:
        if role in decisions:
            return decisions[role]
    if decisions:
        return decisions[sorted(decisions)[0]]
    return "none"


def _repair_action(obj: Any) -> str:
    """Repair marker a curation lane left on the record, when there is one."""
    if not isinstance(obj, dict):
        return "none"
    meta = obj.get("meta")
    if isinstance(meta, dict):
        for key in ("curation_action", "transform_action", "repair_action"):
            value = meta.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if meta.get("spike_events_resorted"):
            return "spike_events_resorted"
    return "none"


def iter_records(root: Path) -> Iterable[tuple[str, int, Any]]:
    """Yield ``(relative_path, line_number, parsed_record)`` for the corpus."""
    for path in jsonl_paths(root):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line, parse_constant=reject_json_constant)
            except (json.JSONDecodeError, ValueError):
                yield rel, number, None
                continue
            yield rel, number, obj


def build_sample(cleaned: Path, per_stratum: int = DEFAULT_PER_STRATUM) -> dict[str, Any]:
    """Stratify by factory x record kind x safety decision, sample deterministically."""
    cleaned = Path(cleaned).resolve()
    if per_stratum < 1:
        raise GateError("--per-stratum must be at least 1")

    buckets: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for rel, number, obj in iter_records(cleaned):
        where = f"{rel}:{number}"
        factory = rel.split("/")[0] if "/" in rel else "_root"
        if obj is None:
            kind = "unparsable"
            decision = "none"
            repair = "none"
            digest = sha256_hex(where.encode("utf-8"))
            record_id = None
        else:
            _errors, kind = check_line(obj, where)
            decision = _primary_decision(obj, kind)
            repair = _repair_action(obj)
            digest = sha256_hex(training_audit.canonical_blob(obj).encode("utf-8"))
            record_id = canonical_record_id(obj) if isinstance(obj, dict) else None
        buckets[(factory, kind, decision, repair)].append(
            {
                "source": where,
                "record_id": record_id,
                "record_sha256": digest,
            }
        )

    strata: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    for key in sorted(buckets):
        factory, kind, decision, repair = key
        population = buckets[key]
        # Content-derived order: stable across runs, independent of file order.
        chosen = sorted(population, key=lambda item: (item["record_sha256"], item["source"]))[
            :per_stratum
        ]
        strata.append(
            {
                "factory": factory,
                "kind": kind,
                "decision": decision,
                "repair_action": repair,
                "population": len(population),
                "sampled": len(chosen),
            }
        )
        for item in chosen:
            items.append(
                {
                    "factory": factory,
                    "kind": kind,
                    "decision": decision,
                    "repair_action": repair,
                    **item,
                }
            )

    return {
        "schema": SAMPLE_SCHEMA,
        "generated_by": f"{TOOL_NAME}/{TOOL_VERSION}",
        "cleaned_dir": str(cleaned),
        "corpus_digest": corpus_digest(cleaned),
        "per_stratum": per_stratum,
        "strata_count": len(strata),
        "sampled_records": len(items),
        "strata": strata,
        "items": items,
    }


def review_template(sample: dict[str, Any]) -> dict[str, Any]:
    """A fill-in-the-blanks verdict file for the recorded sample."""
    return {
        "schema": REVIEW_SCHEMA,
        "reviewer": "",
        "reviewed_at": "",
        "corpus_digest": sample["corpus_digest"],
        "verdicts": {
            item["source"]: {"verdict": "", "notes": ""} for item in sample["items"]
        },
    }


def check_review(
    sample: dict[str, Any], review: Any, digest: str
) -> tuple[list[str], dict[str, Any]]:
    """Return ``(blockers, summary)`` for a reviewed stratified sample."""
    blockers: list[str] = []
    if not isinstance(review, dict):
        return ["REVIEW_NOT_AN_OBJECT"], {"recorded": False}
    schema = review.get("schema")
    if schema is not None and schema != REVIEW_SCHEMA:
        blockers.append(f"REVIEW_SCHEMA_UNSUPPORTED:{schema}")

    reviewer = review.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        blockers.append("REVIEW_REVIEWER_MISSING")

    declared = review.get("corpus_digest")
    if declared != digest:
        blockers.append("REVIEW_CORPUS_MISMATCH")
    if sample.get("corpus_digest") != digest:
        blockers.append("SAMPLE_CORPUS_MISMATCH")

    verdicts = review.get("verdicts")
    if not isinstance(verdicts, dict):
        blockers.append("REVIEW_VERDICTS_MISSING")
        verdicts = {}

    expected = [item["source"] for item in sample.get("items", [])]
    counts: Counter[str] = Counter()
    missing: list[str] = []
    rejected: list[str] = []
    unknown: list[str] = []
    for source in expected:
        entry = verdicts.get(source)
        verdict = entry.get("verdict") if isinstance(entry, dict) else entry
        if not isinstance(verdict, str) or not verdict.strip():
            missing.append(source)
            continue
        lowered = verdict.strip().lower()
        counts[lowered] += 1
        if lowered in REJECT_VERDICTS:
            rejected.append(source)
        elif lowered not in ACCEPT_VERDICTS:
            unknown.append(source)
    extra = sorted(set(verdicts) - set(expected))

    if missing:
        blockers.append(
            f"REVIEW_INCOMPLETE:{len(missing)}/{len(expected)} sampled records unreviewed"
        )
    if unknown:
        blockers.append(f"REVIEW_VERDICT_UNRECOGNIZED:{len(unknown)}")
    if rejected:
        blockers.append(f"REVIEW_REJECTED:{len(rejected)}")

    summary = {
        "recorded": True,
        "reviewer": reviewer if isinstance(reviewer, str) else None,
        "reviewed_at": review.get("reviewed_at"),
        "corpus_digest": declared,
        "sampled_records": len(expected),
        "verdict_counts": dict(sorted(counts.items())),
        "missing": missing[:20],
        "rejected": rejected[:20],
        "unrecognized": unknown[:20],
        "not_in_sample": extra[:20],
    }
    return blockers, summary


# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------


def _run_tool(script: Path, run_dir: Path, *options: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(script), *options, str(run_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _findings(stderr: str, limit: int = 10) -> list[str]:
    return [line for line in stderr.splitlines() if line.strip()][:limit]


def run_gates(cleaned: Path) -> dict[str, Any]:
    """Structural, deep-invariant, and strict corpus gates on one destination."""
    cleaned = Path(cleaned).resolve()
    if not cleaned.is_dir():
        raise GateError(f"not a directory: {cleaned}")
    if not jsonl_paths(cleaned):
        raise GateError(f"cleaned destination holds no *.jsonl: {cleaned}")

    blockers: list[str] = []
    gates: dict[str, Any] = {}

    code, _out, err = _run_tool(VALIDATOR, cleaned)
    gates["structural_validator"] = {
        "tool": "validate_run.py",
        "exit": code,
        "passed": code == 0,
        "findings": _findings(err),
    }
    if code:
        blockers.append(f"STRUCTURAL_VALIDATOR_FAILED:exit {code}")

    code, _out, err = _run_tool(CHECKER, cleaned, "--strict")
    gates["record_invariants"] = {
        "tool": "check_records.py --strict",
        "exit": code,
        "passed": code == 0,
        "findings": _findings(err),
    }
    if code:
        blockers.append(f"RECORD_INVARIANTS_FAILED:exit {code}")

    report = training_audit.audit_run(cleaned)
    gates["training_audit"] = {
        "tool": "training_audit.py --strict",
        "passed": bool(report["training_ready"]),
        "blockers": list(report["blockers"]),
    }
    if not report["training_ready"]:
        blockers.append(f"TRAINING_NOT_READY:{len(report['blockers'])} audit blockers")

    exact_duplicates = report.get("exact_duplicates") or []
    gates["exact_duplicates"] = {
        "passed": not exact_duplicates,
        "count": len(exact_duplicates),
        "examples": exact_duplicates[:5],
    }
    if exact_duplicates:
        blockers.append(f"EXACT_DUPLICATES:{len(exact_duplicates)}")

    identity = report.get("identity") or {}
    collisions = identity.get("duplicates") or []
    gates["canonical_id_collisions"] = {
        "passed": not collisions,
        "count": len(collisions),
        "examples": collisions[:5],
    }
    if collisions:
        blockers.append(f"CANONICAL_ID_COLLISIONS:{len(collisions)}")

    missing_ids = identity.get("missing_top_level", 0)
    gates["canonical_id_coverage"] = {
        "passed": not missing_ids,
        "coverage_pct": identity.get("coverage_pct", 0),
        "missing_top_level": missing_ids,
        "examples": (identity.get("missing_examples") or [])[:5],
    }
    if missing_ids:
        blockers.append(f"CANONICAL_ID_COVERAGE:{missing_ids} records lack a top-level id")

    return {
        "gates": gates,
        "blockers": blockers,
        "audit": report,
        "training_ready": bool(report["training_ready"]),
    }


def _corpus_counts(report: dict[str, Any]) -> dict[str, Any]:
    totals = report.get("totals") or {}
    factories = report.get("factories") or {}
    return {
        "files": totals.get("files", 0),
        "records": totals.get("records", 0),
        "bytes": totals.get("bytes", 0),
        "by_kind": dict(totals.get("by_kind") or {}),
        "by_factory": {
            name: bucket.get("records", 0) for name, bucket in sorted(factories.items())
        },
    }


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------


def build_manifest(
    *,
    plan: dict[str, Any],
    composition: dict[str, Any],
    lane_manifests: dict[str, Any],
    gate_result: dict[str, Any],
    sample: dict[str, Any],
    review: dict[str, Any] | None,
    blockers: Sequence[str],
) -> dict[str, Any]:
    report = gate_result["audit"]
    counts = _corpus_counts(report)
    counts["lane_actions"] = lane_manifests["actions_by_lane"]
    counts["exclusions"] = len(lane_manifests["exclusions"])
    counts["quarantines"] = len(lane_manifests["quarantines"])
    counts["sampled_for_review"] = sample["sampled_records"]
    counts["review_strata"] = sample["strata_count"]

    return {
        "schema": MANIFEST_SCHEMA,
        "generated_by": f"{TOOL_NAME}/{TOOL_VERSION}",
        "plan": {
            "path": str(plan["plan_path"]),
            "sha256": plan["plan_sha256"],
            "source_run": plan["source_run"],
        },
        "cleaned_dir": str(composition["destination"]),
        "corpus_digest": sample["corpus_digest"],
        "composition_order": composition["composition_order"],
        "transform_versions": plan["transform_versions"],
        "counts": counts,
        "inputs": composition["inputs"],
        "outputs": composition["outputs"],
        "supersessions": composition["supersessions"],
        "exclusions": lane_manifests["exclusions"],
        "quarantines": lane_manifests["quarantines"],
        "exclusion_reason_codes": lane_manifests["reason_codes"],
        "lanes_without_record_manifest": lane_manifests["lanes_without_manifest"],
        "gates": gate_result["gates"],
        "review": review if review is not None else {"recorded": False},
        "blockers": list(blockers),
        "training_ready": gate_result["training_ready"],
        "promotion": None,
    }


# ---------------------------------------------------------------------------
# subcommands
# ---------------------------------------------------------------------------


def cmd_integrate(args: argparse.Namespace) -> int:
    if args.per_stratum < 1:
        raise GateError("--per-stratum must be at least 1")
    plan = load_plan(Path(args.plan))
    destination = Path(args.cleaned_out).resolve()
    _assert_new_destination(destination, "cleaned destination")
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent)
    )
    staged = stage_root / "tree"
    try:
        composition = compose(plan, staged, logical_destination=destination)
        lane_manifests = collect_lane_manifests(plan)
        gate_result = run_gates(staged)
        sample = build_sample(staged, args.per_stratum)
        sample["cleaned_dir"] = str(destination)

        blockers = list(gate_result["blockers"])
        blockers.append("REVIEW_NOT_RECORDED")

        manifest = build_manifest(
            plan=plan,
            composition=composition,
            lane_manifests=lane_manifests,
            gate_result=gate_result,
            sample=sample,
            review=None,
            blockers=blockers,
        )
        _write_json(staged / MANIFEST_FILENAME, manifest)
        _write_json(staged / SAMPLE_FILENAME, sample)
        _write_json(staged / REVIEW_FILENAME, review_template(sample))

        # Publish only a complete tree. A copy, manifest, gate, or sidecar
        # failure leaves the requested destination absent and retryable.
        _assert_new_destination(destination, "cleaned destination")
        staged.rename(destination)
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)

    summary = {
        "cleaned_out": str(destination),
        "corpus_digest": sample["corpus_digest"],
        "training_ready": gate_result["training_ready"],
        "gate_blockers": gate_result["blockers"],
        "counts": manifest["counts"],
        "review_sample": str(destination / SAMPLE_FILENAME),
        "review_template": str(destination / REVIEW_FILENAME),
        "manifest": str(destination / MANIFEST_FILENAME),
        "next_step": (
            "record a verdict for every sampled record, then run "
            f"'{TOOL_NAME}.py promote --cleaned {destination} --review <file> "
            "--curated-out <new path>'"
        ),
    }
    print(json.dumps(summary, indent=2))
    return 0 if gate_result["training_ready"] else 1


def _promotion_outputs(curated: Path) -> list[dict[str, Any]]:
    entries = []
    for path in sorted(curated.rglob("*")):
        if not path.is_file():
            continue
        entries.append(
            {
                "path": path.relative_to(curated).as_posix(),
                "sha256": file_sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    return entries


def cmd_promote(args: argparse.Namespace) -> int:
    cleaned = Path(args.cleaned).resolve()
    curated = Path(args.curated_out).resolve()
    if not cleaned.is_dir():
        raise GateError(f"not a directory: {cleaned}")
    _assert_new_destination(curated, "curated destination")

    manifest_path = cleaned / MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise GateError(
            f"{cleaned} has no {MANIFEST_FILENAME}; run '{TOOL_NAME}.py integrate' first"
        )
    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise GateError(f"{manifest_path}: manifest must be a JSON object")

    sample_path = cleaned / SAMPLE_FILENAME
    if not sample_path.is_file():
        raise GateError(f"{cleaned} has no {SAMPLE_FILENAME}; run '{TOOL_NAME}.py integrate' first")
    sample = _load_json(sample_path)
    if not isinstance(sample, dict) or not isinstance(sample.get("items"), list):
        raise GateError(f"{sample_path}: review sample must be an object with an 'items' list")

    review = _load_json(Path(args.review))
    digest = corpus_digest(cleaned)
    gate_result = run_gates(cleaned)
    review_blockers, review_summary = check_review(sample, review, digest)

    blockers = list(gate_result["blockers"]) + review_blockers
    manifest["corpus_digest"] = digest
    manifest["gates"] = gate_result["gates"]
    counts = manifest.get("counts")
    if not isinstance(counts, dict):
        counts = {}
    counts.update(_corpus_counts(gate_result["audit"]))
    manifest["counts"] = counts
    manifest["review"] = review_summary
    manifest["training_ready"] = gate_result["training_ready"]
    manifest["blockers"] = blockers

    if blockers:
        _write_json(manifest_path, manifest)
        print(
            json.dumps(
                {
                    "promoted": False,
                    "cleaned": str(cleaned),
                    "curated_out": str(curated),
                    "blockers": blockers,
                    "manifest": str(manifest_path),
                },
                indent=2,
            )
        )
        return 1

    try:
        promotion = promote_module.promote_run(cleaned, curated)
    except ValueError as exc:
        raise GateError(str(exc)) from exc

    manifest["promotion"] = {
        "curated_dir": str(curated),
        "promoter": "pipelines/promote.py",
        "files": promotion["files"],
        "records": promotion["records"],
        "resorted": promotion["resorted"],
        "outputs": _promotion_outputs(curated),
    }
    manifest["promotion"]["corpus_digest"] = corpus_digest(curated)

    # Hashes are taken before the review evidence lands, so the manifest never
    # has to hash itself.
    _write_json(manifest_path, manifest)
    _write_json(curated / MANIFEST_FILENAME, manifest)
    _write_json(curated / SAMPLE_FILENAME, sample)
    _write_json(curated / REVIEW_FILENAME, review)

    print(
        json.dumps(
            {
                "promoted": True,
                "cleaned": str(cleaned),
                "curated_out": str(curated),
                "corpus_digest": manifest["promotion"]["corpus_digest"],
                "files": promotion["files"],
                "records": promotion["records"],
                "reviewer": review_summary.get("reviewer"),
                "manifest": str(curated / MANIFEST_FILENAME),
            },
            indent=2,
        )
    )
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compose curation lanes into one new cleaned destination, gate it, "
            "and promote it to a new curated path."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    integrate = sub.add_parser(
        "integrate",
        help="compose lane outputs in plan order, gate them, record a review sample",
    )
    integrate.add_argument("--plan", required=True, help="integration plan JSON")
    integrate.add_argument(
        "--cleaned-out", required=True, help="brand-new cleaned destination (must not exist)"
    )
    integrate.add_argument(
        "--per-stratum",
        type=int,
        default=DEFAULT_PER_STRATUM,
        help=f"records sampled per stratum (default {DEFAULT_PER_STRATUM})",
    )
    integrate.set_defaults(handler=cmd_integrate)

    promote_cmd = sub.add_parser(
        "promote",
        help="re-gate a cleaned destination and promote it once the sample is reviewed",
    )
    promote_cmd.add_argument(
        "--cleaned", required=True, help="cleaned destination written by 'integrate'"
    )
    promote_cmd.add_argument("--review", required=True, help="reviewed verdict file")
    promote_cmd.add_argument(
        "--curated-out", required=True, help="brand-new curated destination (must not exist)"
    )
    promote_cmd.set_defaults(handler=cmd_promote)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return args.handler(args)
    except GateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
