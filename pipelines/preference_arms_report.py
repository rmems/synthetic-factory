#!/usr/bin/env python3
"""The decision and scan records the gate reports, and their human rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))




@dataclass(frozen=True)
class ArmDecision:
    """One deterministic pair-level decision. ``blocked`` gates the round."""

    source_path: str
    source_line: int
    record_id: str | None
    same_context: bool
    isolation: str | None
    trusted_isolation: str | None
    arm_distance: float | None
    cosine_similarity: float | None
    reason_codes: tuple[str, ...] = ()

    @property
    def blocked(self) -> bool:
        return bool(self.reason_codes)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "source_line": self.source_line,
            "record_id": self.record_id,
            "same_context": self.same_context,
            "isolation": self.isolation,
            "trusted_isolation": self.trusted_isolation,
            "arm_distance": self.arm_distance,
            "cosine_similarity": self.cosine_similarity,
            "reason_codes": list(self.reason_codes),
            "blocked": self.blocked,
        }


@dataclass(frozen=True)
class ArmScan:
    """Per-pair decisions plus aggregate counts for one source."""

    decisions: tuple[ArmDecision, ...] = ()
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def blocked(self) -> bool:
        return bool(self.summary.get("blocked_pairs"))


def render_human(scan: ArmScan) -> str:
    summary = scan.summary
    lines = [
        f"Preference pairs: {summary['preference_pairs']}",
        f"Same-context: {summary['same_context_pairs']} ({summary['context_purity_pct']}%)",
        f"Two-session attested: {summary['two_session_pairs']}",
        f"Reservation-bound two-session: {summary['trusted_two_session_pairs']}",
        f"Min arm distance required: > {summary['min_arm_distance']}",
        f"Observed arm distance: {summary['observed_min_arm_distance']}"
        f" .. {summary['observed_max_arm_distance']}",
        f"Blocked: {summary['blocked_pairs']}",
    ]
    for decision in scan.decisions:
        location = f"{decision.source_path}:{decision.source_line}"
        record_id = decision.record_id or "<no-id>"
        verdict = "BLOCKED [" + ",".join(decision.reason_codes) + "]" if decision.blocked else "ok"
        lines.append(f"- {location} {record_id}: distance={decision.arm_distance} {verdict}")
    return "\n".join(lines)
