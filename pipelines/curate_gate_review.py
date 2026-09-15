#!/usr/bin/env python3
"""The stratified human-review sample for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

A cleaned corpus is too large to review row by row, so the gate records a
*sample* a human can actually work through and promotes only once every
sampled row carries a verdict. Two kinds of evidence are stratified together:
the corpus rows themselves (by factory, record kind, safety decision and
repair marker) and the manifest's ``review_candidates`` -- the exclusion,
quarantine and repair decisions the lanes took, which leave no row behind to
look at. Within a stratum the choice is content-ordered by record digest, so
the same corpus always yields byte-identical sample items regardless of file
order.

``review_template`` turns a recorded sample into a fill-in-the-blanks verdict
file and ``check_review`` reads one back, binding it to the corpus and
evidence digests it was taken against so a verdict file cannot be carried over
to a different tree.
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, NamedTuple, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_review")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_records as _records
    from . import training_audit
    from . import validate_run as _validate_run
    from .check_records import canonical_record_id
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_review"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_records as _records
    import training_audit
    import validate_run as _validate_run
    from check_records import canonical_record_id

check_line = _validate_run.check_line

GateError = _contract.GateError
TOOL_NAME = _contract.TOOL_NAME
TOOL_VERSION = _contract.TOOL_VERSION
SAMPLE_SCHEMA = _contract.SAMPLE_SCHEMA
REVIEW_SCHEMA = _contract.REVIEW_SCHEMA
MANIFEST_FILENAME = _contract.MANIFEST_FILENAME
DEFAULT_PER_STRATUM = _contract.DEFAULT_PER_STRATUM
DECISION_ROLE_PRIORITY = _contract.DECISION_ROLE_PRIORITY
EXCLUSION_ACTIONS = _contract.EXCLUSION_ACTIONS
QUARANTINE_ACTIONS = _contract.QUARANTINE_ACTIONS
REPAIR_ACTIONS = _contract.REPAIR_ACTIONS
ACCEPT_VERDICTS = _contract.ACCEPT_VERDICTS
REJECT_VERDICTS = _contract.REJECT_VERDICTS

sha256_hex = _digest.sha256_hex
corpus_digest = _digest.corpus_digest
_load_json = _digest._load_json
iter_records = _records.iter_records

# A stratum key: (evidence, factory, kind, decision, repair, exclusion_reason).
_StratumKey = tuple[str, str, str, str, str, str]


# ---------------------------------------------------------------------------
# what a single row contributes to its stratum
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


def _review_candidates_from_manifest(cleaned: Path) -> list[dict[str, Any]]:
    manifest_path = cleaned / MANIFEST_FILENAME
    if not manifest_path.is_file():
        return []
    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise GateError(f"{manifest_path}: manifest must be a JSON object")
    candidates = manifest.get("review_candidates", [])
    if not isinstance(candidates, list) or not all(
        isinstance(candidate, dict) for candidate in candidates
    ):
        raise GateError(f"{manifest_path}: review_candidates must be a list of objects")
    return candidates


def _manifest_factory(source_path: Any, transform: Any) -> str:
    if isinstance(source_path, str) and source_path.strip():
        parts = Path(source_path).parts
        if "raw" in parts:
            index = parts.index("raw")
            if len(parts) > index + 2:
                return parts[index + 2]
        if len(parts) > 1:
            return parts[0]
    return str(transform or "_manifest")


def _corpus_stratum(rel: str, number: int, obj: Any) -> tuple[_StratumKey, dict[str, Any]]:
    """The stratum key and sampled item for one corpus row."""
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
    return (
        ("corpus", factory, kind, decision, repair, "none"),
        {"source": where, "record_id": record_id, "record_sha256": digest},
    )


def _manifest_stratum(candidate: dict[str, Any]) -> tuple[_StratumKey, dict[str, Any]]:
    """The stratum key and sampled item for one manifest review candidate."""
    declared_action = str(candidate.get("action") or "unspecified").strip().lower()
    action = str(candidate.get("review_action") or declared_action).strip().lower()
    reasons = candidate.get("reason_codes")
    if not isinstance(reasons, list):
        reasons = []
    exclusion_reason = "none"
    if action in EXCLUSION_ACTIONS or action in QUARANTINE_ACTIONS:
        exclusion_reason = "+".join(sorted(str(reason) for reason in reasons)) or "UNSPECIFIED"
    transform = candidate.get("transform")
    source_path = candidate.get("source_path")
    source_line = candidate.get("source_line")
    digest = sha256_hex(training_audit.canonical_blob(candidate).encode("utf-8"))
    source = (
        f"manifest:{candidate.get('lane_order')}:{transform}:"
        f"{source_path}:{source_line}:{digest[:16]}"
    )
    repair = action if action in REPAIR_ACTIONS else "none"
    factory = _manifest_factory(source_path, transform)
    kind = str(candidate.get("record_kind") or "manifest_decision")
    return (
        ("manifest", factory, kind, action, repair, exclusion_reason),
        {
            "source": source,
            "record_id": candidate.get("output_id"),
            "record_sha256": digest,
            "manifest_entry": candidate,
        },
    )


# ---------------------------------------------------------------------------
# the sample
# ---------------------------------------------------------------------------


def _manifest_evidence_digest(cleaned: Path) -> str | None:
    """The evidence digest the cleaned manifest recorded, when it has one."""
    manifest_path = cleaned / MANIFEST_FILENAME
    if not manifest_path.is_file():
        return None
    manifest = _load_json(manifest_path)
    if isinstance(manifest, dict):
        value = manifest.get("evidence_digest")
        if isinstance(value, str):
            return value
    return None


def _resolve_review_inputs(
    cleaned: Path,
    review_candidates: Sequence[dict[str, Any]] | None,
    evidence_digest: str | None,
) -> tuple[Sequence[dict[str, Any]], str | None]:
    """Fall back to the cleaned manifest for candidates and evidence digest."""
    if review_candidates is None:
        review_candidates = _review_candidates_from_manifest(cleaned)
        if evidence_digest is None:
            evidence_digest = _manifest_evidence_digest(cleaned)
    if not all(isinstance(candidate, dict) for candidate in review_candidates):
        raise GateError("review candidates must be objects")
    return review_candidates, evidence_digest


def _sample_stratum(
    key: _StratumKey, population: list[dict[str, Any]], per_stratum: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Describe one stratum and take its content-ordered sample."""
    evidence, factory, kind, decision, repair, exclusion_reason = key
    # Content-derived order: stable across runs, independent of file order.
    chosen = sorted(
        population,
        key=lambda sampled: (sampled["record_sha256"], sampled["source"]),
    )[:per_stratum]
    facets = {
        "evidence": evidence,
        "factory": factory,
        "kind": kind,
        "decision": decision,
        "repair_action": repair,
        "exclusion_reason": exclusion_reason,
    }
    stratum = {**facets, "population": len(population), "sampled": len(chosen)}
    return stratum, [{**facets, **item} for item in chosen]


def build_sample(
    cleaned: Path,
    per_stratum: int = DEFAULT_PER_STRATUM,
    review_candidates: Sequence[dict[str, Any]] | None = None,
    *,
    evidence_digest: str | None = None,
) -> dict[str, Any]:
    """Stratify corpus and manifest decisions, then sample deterministically."""
    cleaned = Path(cleaned).resolve()
    if per_stratum < 1:
        raise GateError("--per-stratum must be at least 1")
    review_candidates, evidence_digest = _resolve_review_inputs(
        cleaned, review_candidates, evidence_digest
    )

    buckets: dict[_StratumKey, list[dict[str, Any]]] = defaultdict(list)
    for rel, number, obj in iter_records(cleaned):
        key, item = _corpus_stratum(rel, number, obj)
        buckets[key].append(item)
    for candidate in review_candidates:
        key, item = _manifest_stratum(candidate)
        buckets[key].append(item)

    strata: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    for key in sorted(buckets):
        stratum, chosen = _sample_stratum(key, buckets[key], per_stratum)
        strata.append(stratum)
        items.extend(chosen)

    return {
        "schema": SAMPLE_SCHEMA,
        "generated_by": f"{TOOL_NAME}/{TOOL_VERSION}",
        "cleaned_dir": str(cleaned),
        "corpus_digest": corpus_digest(cleaned),
        "evidence_digest": evidence_digest,
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
        "evidence_digest": sample.get("evidence_digest"),
        "verdicts": {item["source"]: {"verdict": "", "notes": ""} for item in sample["items"]},
    }


# ---------------------------------------------------------------------------
# reading a review back
# ---------------------------------------------------------------------------


class _VerdictTally(NamedTuple):
    """How the recorded verdicts land against the sampled sources."""

    counts: Counter[str]
    missing: list[str]
    rejected: list[str]
    unknown: list[str]


def _review_header_blockers(
    sample: dict[str, Any], review: dict[str, Any], digest: str, evidence_digest: str
) -> list[str]:
    """Schema, reviewer and the four digest bindings, in reporting order."""
    blockers: list[str] = []
    schema = review.get("schema")
    if schema is not None and schema != REVIEW_SCHEMA:
        blockers.append(f"REVIEW_SCHEMA_UNSUPPORTED:{schema}")

    reviewer = review.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        blockers.append("REVIEW_REVIEWER_MISSING")

    if review.get("corpus_digest") != digest:
        blockers.append("REVIEW_CORPUS_MISMATCH")
    if sample.get("corpus_digest") != digest:
        blockers.append("SAMPLE_CORPUS_MISMATCH")
    if sample.get("evidence_digest") != evidence_digest:
        blockers.append("SAMPLE_EVIDENCE_MISMATCH")
    if review.get("evidence_digest") != evidence_digest:
        blockers.append("REVIEW_EVIDENCE_MISMATCH")
    return blockers


def _verdict_tally(verdicts: dict[str, Any], expected: Sequence[str]) -> _VerdictTally:
    """Classify each sampled source's recorded verdict."""
    tally = _VerdictTally(Counter(), [], [], [])
    for source in expected:
        entry = verdicts.get(source)
        verdict = entry.get("verdict") if isinstance(entry, dict) else entry
        if not isinstance(verdict, str) or not verdict.strip():
            tally.missing.append(source)
            continue
        lowered = verdict.strip().lower()
        tally.counts[lowered] += 1
        if lowered in REJECT_VERDICTS:
            tally.rejected.append(source)
        elif lowered not in ACCEPT_VERDICTS:
            tally.unknown.append(source)
    return tally


def check_review(
    sample: dict[str, Any], review: Any, digest: str, evidence_digest: str
) -> tuple[list[str], dict[str, Any]]:
    """Return ``(blockers, summary)`` for a reviewed stratified sample."""
    if not isinstance(review, dict):
        return ["REVIEW_NOT_AN_OBJECT"], {"recorded": False}
    blockers = _review_header_blockers(sample, review, digest, evidence_digest)

    verdicts = review.get("verdicts")
    if not isinstance(verdicts, dict):
        blockers.append("REVIEW_VERDICTS_MISSING")
        verdicts = {}

    expected = [item["source"] for item in sample.get("items", [])]
    tally = _verdict_tally(verdicts, expected)
    extra = sorted(set(verdicts) - set(expected))

    if tally.missing:
        blockers.append(
            f"REVIEW_INCOMPLETE:{len(tally.missing)}/{len(expected)} sampled records unreviewed"
        )
    if tally.unknown:
        blockers.append(f"REVIEW_VERDICT_UNRECOGNIZED:{len(tally.unknown)}")
    if tally.rejected:
        blockers.append(f"REVIEW_REJECTED:{len(tally.rejected)}")

    reviewer = review.get("reviewer")
    summary = {
        "recorded": True,
        "reviewer": reviewer if isinstance(reviewer, str) else None,
        "reviewed_at": review.get("reviewed_at"),
        "corpus_digest": review.get("corpus_digest"),
        "evidence_digest": review.get("evidence_digest"),
        "sampled_records": len(expected),
        "verdict_counts": dict(sorted(tally.counts.items())),
        "missing": tally.missing[:20],
        "rejected": tally.rejected[:20],
        "unrecognized": tally.unknown[:20],
        "not_in_sample": extra[:20],
    }
    return blockers, summary


if __package__:
    _expose_package_sibling(__name__)
