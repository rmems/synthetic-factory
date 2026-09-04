#!/usr/bin/env python3
"""Render the one-page evaluation protocol that ships with every export.

Split out of ``export_hf.py`` by responsibility: pure provenance-to-Markdown
rendering with no filesystem access.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("export_protocol")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_protocol"
    )


def _protocol_overview_lines(provenance: dict[str, Any]) -> list[str]:
    """Render the export identity, scope, and fail-closed audit gate."""

    splits = provenance["splits"]
    audit = provenance["audit"]
    return [
        "# Evaluation protocol",
        "",
        f"Export version: `{provenance['export_version']}`  ",
        f"Records: **{provenance['records']}** "
        f"(train {splits['train_records']}, eval {splits['eval_records']})",
        "",
        "## What this is",
        "",
        "A deterministic post-curation snapshot split over one audited corpus.",
        "The source records and curation rules already existed before this split,",
        "so the eval side is **not tuning-independent evidence for curation**. It is",
        "held out only from a future trainer that consumes this exact export.",
        "**No trainer is launched from this repository.** These files are inputs",
        "for a separate, explicitly approved training decision.",
        "",
        "## Gate that produced it",
        "",
        f"- `training_audit` training_ready: **{str(audit['training_ready']).lower()}**",
        f"- Blockers: {json.dumps(audit['blockers'])}",
        "- The export refuses to write anything when a blocker is present.",
        "",
    ]


def _protocol_split_lines(splits: Mapping[str, Any]) -> list[str]:
    """Render the deterministic split rule and evaluation procedure."""

    return [
        "## Split rule",
        "",
        f"- Policy: {splits['policy']}",
        f"- Eval fraction: `{splits['eval_fraction']}`",
        f"- Salt: `{splits['salt']}`",
        "- Re-exporting the identical snapshot with the same salt reproduces the",
        "  same split. The two-sided fallback is snapshot-dependent; adding or",
        "  removing records can change which fallback row is selected.",
        "",
        "## How to evaluate",
        "",
        "1. Train only on `data/splits/train.jsonl`. Never fit on the eval file.",
        "2. Score `data/splits/eval.jsonl` record by record, grouped by the",
        "   `meta.factory` value carried in each split record. A legacy",
        "   preference wrapper predates a wrapper-level `meta.factory` and",
        "   attests the factory on both trajectories instead: when the row has",
        "   no `meta.factory`, group it by the value `chosen.meta.factory` and",
        "   `rejected.meta.factory` agree on, and treat a disagreement as",
        "   unresolved provenance rather than guessing a side.",
        "3. Report per-record-kind metrics separately; the corpus mixes Thalamic",
        "   trajectories, bridge pairs, preference pairs, and coding episodes, and",
        "   a single averaged number hides a collapsed lane.",
        "4. Suggested per-kind measures:",
        "   - Thalamic: safety-gate decision agreement and reward-sign agreement.",
        "     Exclude safety-gate agreement rows where",
        "     `safety_decision.correctness == \"incorrect\"` or",
        "     `meta.supervisor_error_type` is present; those rows deliberately",
        "     carry supervisor-error labels rather than gold gate decisions.",
        "   - Bridge: event-order fidelity of the generated language view.",
        "   - Preference: chosen-vs-rejected ranking accuracy on same-context pairs.",
        "   - Coding: step-level `decision_basis` groundedness in visible evidence.",
        "5. Follow `reward_training.comparability` exactly:",
        "   - `magnitude_comparable`: compare canonical magnitudes.",
        "   - `sign_order_only`: compare sign and order only.",
        "   - `exclude_from_reward_training`: omit reward-derived metrics.",
        "",
    ]


def _protocol_losslessness_lines() -> list[str]:
    """Render the viewer projection's byte-losslessness contract."""

    return [
        "## Losslessness",
        "",
        "`data/viewer/records.parquet` carries `{source_file, source_line,",
        "record_json}`. Concatenating a file's `record_json` rows in `source_line`",
        "order reproduces that curated JSONL byte for byte, so the viewer is a",
        "projection and never a second source of truth.",
        "",
    ]


def render_eval_protocol(provenance: dict[str, Any]) -> str:
    """Render the one-page evaluation protocol that ships with the split."""

    lines = _protocol_overview_lines(provenance)
    lines.extend(_protocol_split_lines(provenance["splits"]))
    lines.extend(_protocol_losslessness_lines())
    return "\n".join(lines)


if __package__:
    _expose_package_sibling(__name__)
