#!/usr/bin/env python3
"""Per-line JSONL framing, lane decisions, and manifest accounting for compose runs."""

from __future__ import annotations

import sys
from typing import Any, Callable

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_run_lines")
    from . import compose_contract as _contract
    from . import compose_curated_run_context as _run_context
    from .compose_curated_context import SemanticRegistry, SourceLineCoordinate
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_run_lines"
    )
    import compose_contract as _contract
    import compose_curated_run_context as _run_context
    from compose_curated_context import SemanticRegistry, SourceLineCoordinate

ACTION_EXCLUDED = _contract.ACTION_EXCLUDED
COMPOSE_NAME = _contract.COMPOSE_NAME
COMPOSE_VERSION = _contract.COMPOSE_VERSION
LANE_ORDER = _contract.LANE_ORDER
RECORDS_DIRNAME = _contract.RECORDS_DIRNAME
ComposeDecision = _contract.ComposeDecision
ComposeError = _contract.ComposeError
canonical_json = _contract.canonical_json
sha256_hex = _contract.sha256_hex
ComposeRunHooks = _run_context.ComposeRunHooks
ComposeRunState = _run_context.ComposeRunState
PhysicalSourceLine = _run_context.PhysicalSourceLine
RetainedLineContext = _run_context.RetainedLineContext
SourceLineContext = _run_context.SourceLineContext
SourceServices = _run_context.SourceServices


def jsonl_physical_lines(raw_file: bytes) -> list[bytes]:
    physical_lines = raw_file.split(b"\n")
    terminated_lines = len(physical_lines) - 1
    if physical_lines and physical_lines[-1] == b"":
        physical_lines.pop()
    framed = min(terminated_lines, len(physical_lines))
    physical_lines[:framed] = map(without_terminal_cr, physical_lines[:framed])
    return physical_lines


def without_terminal_cr(physical_line: bytes) -> bytes:
    """Remove JSONL framing's CR only when the line ended in CRLF."""

    return physical_line[:-1] if physical_line.endswith(b"\r") else physical_line


def new_manifest_entry(context: SourceLineContext, source_sha256: str) -> dict[str, Any]:
    return {
        "compose_name": COMPOSE_NAME,
        "compose_version": COMPOSE_VERSION,
        "lane_order": list(LANE_ORDER),
        "source_path": context.relative,
        "source_line": context.line_number,
        "source_sha256": source_sha256,
        "source_file_sha256": context.source_file_sha256,
    }


def claim_output_id(state: ComposeRunState, output_id: Any, location: str) -> None:
    if output_id is None:
        return
    previous = state.emitted_ids.get(output_id)
    if previous is not None:
        raise ComposeError(f"canonical ID collision {output_id!r}: {previous} and {location}")
    state.emitted_ids[output_id] = location


def record_retained_line(
    state: ComposeRunState,
    decision: ComposeDecision,
    context: RetainedLineContext,
    claim_output_id_fn: Callable[..., None] = claim_output_id,
) -> None:
    line = canonical_json(decision.record)
    claim_output_id_fn(state, decision.output_id, context.location)
    context.emitted.append(line)
    context.entry.update(
        {
            "output_path": f"{RECORDS_DIRNAME}/{context.relative}",
            "output_line": len(context.emitted),
            "output_id": decision.output_id,
            "output_sha256": sha256_hex(line.encode("utf-8")),
        }
    )
    state.counts["retained"] += 1
    if decision.reward_sidecar is not None:
        context.entry["reward_sidecar_id"] = decision.reward_sidecar["sidecar_id"]
        state.sidecar_lines.append(canonical_json(decision.reward_sidecar))


def record_excluded_line(
    state: ComposeRunState, decision: ComposeDecision, entry: dict[str, Any]
) -> None:
    entry.update(
        {
            "output_path": None,
            "output_line": None,
            "output_id": None,
            "output_sha256": None,
        }
    )
    state.counts["excluded"] += 1
    for reason in decision.reason_codes or ("compose.unspecified",):
        state.exclusions[reason] += 1


def mill_quarantined_decision(finding: Any) -> ComposeDecision:
    reasons = list(finding.reason_codes)
    stage = {
        "lane": "source",
        "transform_name": COMPOSE_NAME,
        "transform_version": COMPOSE_VERSION,
        "action": ACTION_EXCLUDED,
        "reason_codes": reasons,
        "classification": "foreign_mill_quarantined",
        "detail": finding.as_dict(),
    }
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        tuple(reasons),
        (stage,),
        None,
        None,
    )


def line_decision(
    state: ComposeRunState,
    source_line: PhysicalSourceLine,
    services: SourceServices,
    hooks: ComposeRunHooks,
) -> ComposeDecision:
    context = source_line.context
    finding = None
    if context.mill_findings is not None:
        finding = context.mill_findings.get((context.relative, context.line_number))
    if finding is not None:
        return hooks.mill_quarantined_decision(finding)
    return services.compose_source_line(
        source_line.payload,
        SourceLineCoordinate(context.relative, context.line_number, context.source_file_sha256),
        calibration_catalog=context.catalog,
        semantics=SemanticRegistry(state.seen_source_semantics, state.seen_curated_semantics),
    )


def account_lane_actions(state: ComposeRunState, decision: ComposeDecision) -> None:
    for stage in decision.stages:
        lane = stage["lane"]
        if lane in state.lane_actions:
            state.lane_actions[lane][stage["action"]] += 1


if __package__:
    _expose_package_sibling(__name__)
