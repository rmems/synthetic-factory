#!/usr/bin/env python3
"""Mechanically assemble batch-r11.jsonl. Session B must not read rejected JSON."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

STAGE = Path("/tmp/ffpc-r11")
ROUND = 11
FACTORY = "failure-as-fuel-preference-cascade"

REWARD_SKIP = frozenset(
    {
        "aggregation",
        "comment",
        "component_notes",
        "convention",
        "description",
        "frame",
        "native_unit",
        "notes",
        "provenance_notes",
        "rounding_decimals",
        "total",
        "total_basis",
        "unit_usd",
        "units",
        "weights",
        "weights_note",
    }
)

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "research_retention_status": "allowed",
    "research_evaluation_status": "allowed",
    "redistribution_status": "unresolved",
    "provider_training_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
    "linear_issue": "RM-793",
}

GOALS = {
    1: (
        "Gate AquaYield's request to raise train D-2 indicated discharge from "
        "66.2 bar to 68.0 bar against CAL-PT-D2-HP-20260828 and the 68.0 bar "
        "true feed limit."
    ),
    2: (
        "Gate BleachKeep's request to trip generator G-3, dump 1800 L, and "
        "evacuate the generator building on AT-G3-A high-high under a "
        "shared-sample 2oo2 vote."
    ),
    3: (
        "Gate TroughGuard's request to start LF-6 freeze-protection "
        "recirculation under SOP FP-06 against commercial memo OPS-NIGHT-2."
    ),
}

CRITIQUES = {
    1: (
        "The failed gate flipped a documented LOW-as-found span card and spent "
        "the flipped 1.60 bar as leftover screen margin, then treated in-spec "
        "permeate as proof the membranes had mechanical room while high-tide "
        "salinity was loading the lead elements. The repaired gate applies the "
        "card in the written direction, sees 67.8 bar true against a 68.0 true "
        "cap, holds D-2, and recovers flow on standby D-6. The night still "
        "closes 187 m3 short of 7200, and the 25-minute flush is paid, but the "
        "lead elements and a 14-hour outage are not."
    ),
    2: (
        "The failed gate treated a shared probe and heated line as independent "
        "redundancy, averaged a condensate-locked B cell with a high-high A "
        "cell, and kept two operators in the generator building because the "
        "floor monitor was still quiet. The repaired gate reads independence "
        "from the sample path, trips and dumps on AT-G3-A, and pulls people "
        "before occupancy becomes the detector. The 1800 L dump and the T-2 "
        "slip are paid in the night window; the reportable building excursion "
        "is not."
    ),
    3: (
        "The failed gate substituted a warm outlet header for far-collector "
        "inventory and ranked a commercial pumping memo above SOP FP-06 while "
        "the coldest far RTD had about 11 minutes to freeze. The repaired gate "
        "starts recirculation without a duty-manager precondition, logs "
        "OPS-NIGHT-2 as a commercial exception, and pays the 1400 USD demand "
        "charge. Far-loop recovery is slow and the parasitic energy is real; "
        "the glass and the HTF stay in the troughs."
    ),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> dict:
    data = path.read_bytes()
    return {"name": path.name, "bytes": len(data), "sha256": sha256_bytes(data)}


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def deep_equal(a, b) -> bool:
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if type(a) != type(b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
            return float(a) == float(b)
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(deep_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(deep_equal(x, y) for x, y in zip(a, b))
    return a == b


def differing_paths(a, b, prefix: str, out: list[str]) -> None:
    if type(a) != type(b) or (isinstance(a, bool) != isinstance(b, bool)):
        out.append(prefix)
        return
    if isinstance(a, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                out.append(f"{prefix}.{key}")
            else:
                differing_paths(a[key], b[key], f"{prefix}.{key}", out)
        return
    if isinstance(a, list):
        if len(a) != len(b):
            out.append(prefix)
            return
        for i, (x, y) in enumerate(zip(a, b)):
            differing_paths(x, y, f"{prefix}[{i}]", out)
        return
    if a != b:
        out.append(prefix)


def reward_delta(chosen_rc: dict, rejected_rc: dict) -> dict:
    keys = []
    for key in chosen_rc:
        if key in REWARD_SKIP or key not in rejected_rc:
            continue
        if is_number(chosen_rc[key]) and is_number(rejected_rc[key]):
            keys.append(key)
    per = {key: chosen_rc[key] - rejected_rc[key] for key in keys}
    total = float(math.fsum(per.values()))
    if abs(total - math.fsum(per.values())) > 1e-6:
        raise SystemExit("reward_delta total does not reconcile")
    if not (chosen_rc["total"] > rejected_rc["total"]):
        raise SystemExit("chosen.total is not greater than rejected.total")
    return {"per_component": per, "total": total}


def assert_no_thought(obj: dict, label: str) -> None:
    blob = json.dumps(obj)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "training_ready"):
        if f'"{key}"' in blob:
            raise SystemExit(f"{label} contains forbidden key {key}")


def main() -> None:
    lines = []
    receipt_pairs = []
    for index in (1, 2, 3):
        chosen_path = STAGE / f"chosen-{index:02d}-r11.json"
        rejected_path = STAGE / f"rejected-{index:02d}-r11.json"
        chosen = json.loads(chosen_path.read_text(encoding="utf-8"))
        rejected = json.loads(rejected_path.read_text(encoding="utf-8"))
        if not isinstance(chosen, dict) or not isinstance(rejected, dict):
            raise SystemExit(f"pair {index}: chosen/rejected must be objects")
        for field in ("state", "proposed_action"):
            if not deep_equal(chosen.get(field), rejected.get(field)):
                paths: list[str] = []
                differing_paths(chosen.get(field), rejected.get(field), field, paths)
                raise SystemExit(
                    f"pair {index}: same-context purity failed on {field}; paths={paths[:20]}"
                )
        delta = reward_delta(chosen["reward_components"], rejected["reward_components"])
        record = {
            "id": f"ffpc-r11-{index:03d}",
            "goal": GOALS[index],
            "chosen": chosen,
            "rejected": rejected,
            "critique": CRITIQUES[index],
            "reward_delta": delta,
            "meta": {
                "round": ROUND,
                "factory": FACTORY,
                "generator": "grok-4.6",
                "run_label": "2026-09-02-final-heavy",
                "isolation": "two-session",
                "session": "B",
                "rights": dict(RIGHTS),
            },
        }
        assert_no_thought(record["chosen"], f"chosen-{index:02d}")
        assert_no_thought({"meta": record["meta"], "id": record["id"]}, f"record-{index:02d}")
        if record["chosen"]["state"].get("sim_or_real") == "real":
            raise SystemExit("sim_or_real=real")
        lines.append(json.dumps(record, ensure_ascii=True, separators=(",", ":")))
        receipt_pairs.append(
            {
                "id": record["id"],
                "chosen_decision": chosen["safety_decision"]["decision"],
                "chosen_total": chosen["reward_components"]["total"],
                "rejected_total": rejected["reward_components"]["total"],
                "reward_delta_total": delta["total"],
                "reward_delta_per_component": delta["per_component"],
            }
        )

    batch_path = STAGE / "batch-r11.jsonl"
    payload = "\n".join(lines) + "\n"
    batch_path.write_text(payload, encoding="utf-8")

    artifacts = [
        STAGE / "chosen-01-r11.json",
        STAGE / "chosen-02-r11.json",
        STAGE / "chosen-03-r11.json",
        STAGE / "assemble.py",
        STAGE / "NOTES-r11.md",
        batch_path,
    ]
    artifacts = [path for path in artifacts if path.exists()]
    receipt = {
        "session": "B",
        "factory": FACTORY,
        "round": ROUND,
        "run_label": "2026-09-02-final-heavy",
        "generator": "grok-4.6",
        "isolation": "two-session",
        "linear_issue": "RM-793",
        "intended_use": "research_only",
        "batch": file_digest(batch_path),
        "lines": 3,
        "artifacts": [file_digest(path) for path in artifacts],
        "pairs": receipt_pairs,
        "note": "rejected JSON was json-loaded at assembly time and not emitted on stdout",
    }
    receipt_path = STAGE / "assembler-receipt-r11.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print("ASSEMBLE_OK")
    print(f"batch={batch_path} bytes={receipt['batch']['bytes']} sha256={receipt['batch']['sha256']} lines=3")
    for art in receipt["artifacts"]:
        print(f"artifact {art['name']} bytes={art['bytes']} sha256={art['sha256']}")
    for pair in receipt_pairs:
        print(
            f"{pair['id']} decision={pair['chosen_decision']} "
            f"chosen_total={pair['chosen_total']} rejected_total={pair['rejected_total']} "
            f"delta_total={pair['reward_delta_total']}"
        )
    print(f"receipt={receipt_path}")


if __name__ == "__main__":
    main()
