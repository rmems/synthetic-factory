#!/usr/bin/env python3
"""Build, render, and re-verify the published impure-pair audit.

The audit is the public evidence behind a curated preference corpus: every
impure pair by source location and record id, the reason codes behind its
decision, and the counters those rows have to reconcile against.

``build_audit`` derives the document from a scan and ``render_audit_markdown``
publishes it; re-verifying a published document against a later scan is the
separate job of ``preference_audit_diff``. Rendering treats every audited
value as hostile: a record id comes from source JSONL, not from an internal
enum, so it is escaped before it can add table columns or hide a row.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from preference_model import (  # noqa: E402
    ACTION_EXCLUDED,
    ACTION_REPAIRED,
    CurationRun,
    PreferenceCurationError,
)

__all__ = [
    "AUDIT_NAME",
    "AUDIT_SCHEMA_VERSION",
    "build_audit",
    "render_audit_markdown",
]

AUDIT_NAME = "same-context-preference-audit"
AUDIT_SCHEMA_VERSION = "1.1.0"


def _divergent_context_fields(entry: dict[str, Any]) -> list[str]:
    """Return the canonical context fields that differ across the two sides."""

    fields = []
    if entry.get("same_state") is False:
        fields.append("state")
    if entry.get("same_proposed_action") is False:
        fields.append("proposed_action")
    return fields


def build_audit(run: CurationRun) -> dict[str, Any]:
    """Return the public impure-pair audit document for one curation run.

    The document is the machine-readable half of the published audit: every
    impure pair by source location and record id, the reason codes behind its
    curation decision, and the state/proposal split that reconciles a
    ``same_state``-only count against the full same-context count.
    """

    summary = run.summary
    impure_pairs = [
        {
            "source_path": entry["source_path"],
            "source_line": entry["source_line"],
            "source_sha256": entry["source_sha256"],
            "record_id": entry["source_record_id"],
            "action": entry["action"],
            "classification": entry["classification"],
            "reason_codes": list(entry["reason_codes"]),
            "same_state": entry["same_state"],
            "same_proposed_action": entry["same_proposed_action"],
            "divergent_context_fields": _divergent_context_fields(entry),
            "context_diff_paths": list(entry["context_diff_paths"]),
        }
        for entry in run.manifest
        if entry["action"] in (ACTION_REPAIRED, ACTION_EXCLUDED)
        and (
            entry["same_state"] is not True
            or entry["same_proposed_action"] is not True
        )
    ]
    balanced = (
        summary["state_only_divergent_pairs"]
        + summary["proposed_action_only_divergent_pairs"]
        + summary["both_context_fields_divergent_pairs"]
        + summary["context_undetermined_pairs"]
    )
    if balanced != summary["impure_pairs"] or len(impure_pairs) != summary["impure_pairs"]:
        raise PreferenceCurationError(
            "internal error: impure-pair reconciliation does not balance "
            f"({len(impure_pairs)} listed, {balanced} bucketed, "
            f"{summary['impure_pairs']} impure)"
        )
    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "audit": AUDIT_NAME,
        "transform": dict(summary["transform"]),
        "summary": {
            "preference_pairs": summary["preference_records"],
            "impure_pairs": summary["impure_pairs"],
            "same_state_pairs": summary["same_state_pairs"],
            "state_divergent_pairs": summary["state_divergent_pairs"],
            "state_undetermined_pairs": summary["state_undetermined_pairs"],
            "proposed_action_divergent_pairs": summary["proposed_action_divergent_pairs"],
            "proposed_action_undetermined_pairs": summary["proposed_action_undetermined_pairs"],
            "state_only_divergent_pairs": summary["state_only_divergent_pairs"],
            "proposed_action_only_divergent_pairs": summary["proposed_action_only_divergent_pairs"],
            "both_context_fields_divergent_pairs": summary["both_context_fields_divergent_pairs"],
            "context_undetermined_pairs": summary["context_undetermined_pairs"],
            "curated_retained_pairs": summary["retained_pairs"],
            "curated_repaired_pairs": summary["actions"].get(ACTION_REPAIRED, 0),
            "curated_excluded_pairs": summary["excluded_pairs"],
            "retained_context_purity_pct": summary["retained_context_purity_pct"],
        },
        "source_files": [dict(entry) for entry in run.source_files],
        "impure_pairs": impure_pairs,
    }


def _yes_no(value: bool | None) -> str:
    if value is None:
        return "n/a"
    return "yes" if value else "no"


def _markdown_cell_text(value: Any) -> str:
    """Flatten a source-controlled value into exactly one Markdown table cell.

    ``record_id``, ``source_path`` and the reason codes come from the audited
    JSON rather than from a constrained internal enum. A newline ends the
    table row and a ``|`` opens the next cell -- inside a code span too -- so
    a crafted value could otherwise add columns, inject rows, or visually
    hide a record from the published per-pair evidence.
    """

    text = str(value)
    for control in ("\r\n", "\r", "\n", "\t"):
        text = text.replace(control, " ")
    # Backslashes first: escaping only the pipe turns a value that already
    # ends in a backslash into ``\\|``, where the first backslash escapes the
    # second and hands the pipe back to the table parser as a delimiter.
    return text.replace("\\", "\\\\").replace("|", "\\|")


def _markdown_code_cell(value: Any) -> str:
    """Wrap a source-controlled value in a code span it cannot break out of."""

    text = _markdown_cell_text(value)
    # CommonMark closes a code span at the first backtick run matching the
    # opening one, so the fence must be longer than the longest run inside,
    # and a value that starts or ends with a backtick needs the pad space
    # that the reader strips back off.
    longest = max((len(run) for run in re.findall("`+", text)), default=0)
    fence = "`" * (longest + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def render_audit_markdown(audit: dict[str, Any]) -> str:
    """Render the audit document as the published Markdown tables."""

    summary = audit["summary"]
    lines = [
        "| Measure | Pairs |",
        "| --- | ---: |",
        f"| Published preference pairs | {summary['preference_pairs']} |",
        f"| `same_state = false` (state diverges) | {summary['state_divergent_pairs']} |",
        "| `same_proposed_action = false` (proposal diverges) | "
        f"{summary['proposed_action_divergent_pairs']} |",
        f"| Impure pairs (either field diverges) | {summary['impure_pairs']} |",
        f"| - state only | {summary['state_only_divergent_pairs']} |",
        f"| - proposed action only | {summary['proposed_action_only_divergent_pairs']} |",
        f"| - both fields | {summary['both_context_fields_divergent_pairs']} |",
        f"| - context not comparable | {summary['context_undetermined_pairs']} |",
        f"| Curated keep (already identical + repaired) | {summary['curated_retained_pairs']} |",
        f"| Curated exclude | {summary['curated_excluded_pairs']} |",
        f"| Curated same-context purity | {summary['retained_context_purity_pct']:.1f}% |",
        "",
        "| Pair | Source | `same_state` | `same_proposed_action` | Curation | Reason codes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for pair in audit["impure_pairs"]:
        record_id = pair["record_id"]
        # ``0`` and ``false`` are record ids the JSON audit preserves; only
        # a genuinely absent id may be rendered as one.
        identifier = (
            "_(no record id)_"
            if record_id is None
            else _markdown_code_cell(record_id)
        )
        reasons = (
            ", ".join(_markdown_code_cell(code) for code in pair["reason_codes"])
            or "_(none)_"
        )
        location = _markdown_code_cell(
            f"{pair['source_path']}:{pair['source_line']}"
        )
        lines.append(
            f"| {identifier} "
            f"| {location} "
            f"| {_yes_no(pair['same_state'])} "
            f"| {_yes_no(pair['same_proposed_action'])} "
            f"| {_markdown_cell_text(pair['action'])} "
            f"| {reasons} |"
        )
    return "\n".join(lines)
