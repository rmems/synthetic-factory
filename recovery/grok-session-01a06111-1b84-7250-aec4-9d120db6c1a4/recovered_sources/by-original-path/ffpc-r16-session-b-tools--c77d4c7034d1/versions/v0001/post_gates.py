#!/usr/bin/env python3
"""Post-assembly gates. Prints scalars only; never dumps rejected JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path

STAGE = Path("/tmp/ffpc-r16")
BATCH = STAGE / "batch-r16.jsonl"
ROUND_TAG = "r16"


def deep_equal(a, b) -> bool:
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if type(a) != type(b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return float(a) == float(b)
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(deep_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(deep_equal(x, y) for x, y in zip(a, b))
    return a == b


def main() -> int:
    diags = sorted(STAGE.glob(f"diagnosis-*-{ROUND_TAG}.md"))
    if len(diags) != 3:
        print(f"purity gate: FAIL — expected 3 diagnoses, got {len(diags)}", file=sys.stderr)
        return 1
    diag_text = "\n".join(p.read_text(encoding="utf-8") for p in diags)
    errors = []
    lines = [ln for ln in BATCH.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(lines) != 3:
        errors.append(f"batch lines={len(lines)} expected 3")
    for lineno, line in enumerate(lines, 1):
        r = json.loads(line)
        chosen, rejected = r.get("chosen"), r.get("rejected")
        if not isinstance(chosen, dict) or not isinstance(rejected, dict):
            errors.append(f"line {lineno}: chosen/rejected must both be objects")
            continue
        rec_id = r.get("id")
        for field in ("state", "proposed_action"):
            a, b = chosen.get(field), rejected.get(field)
            if a is None or b is None:
                errors.append(f"line {lineno} {rec_id}: missing {field}")
            elif not deep_equal(a, b):
                errors.append(f"line {lineno} {rec_id}: chosen.{field} != rejected.{field}")
        sd = chosen.get("safety_decision")
        rationale = sd.get("rationale", "") if isinstance(sd, dict) else ""
        if rationale and rationale.strip() in diag_text:
            errors.append(f"line {lineno} {rec_id}: rationale verbatim in diagnosis")
        iso = None
        meta = r.get("meta")
        if isinstance(meta, dict):
            iso = meta.get("isolation")
        if iso != "two-session":
            errors.append(f"line {lineno} {rec_id}: meta.isolation={iso!r}")
        rights = meta.get("rights") if isinstance(meta, dict) else None
        if not isinstance(rights, dict) or rights.get("intended_use") != "research_only":
            errors.append(f"line {lineno} {rec_id}: missing research_only rights")
        if rights and rights.get("project_training_policy") != "blocked":
            errors.append(f"line {lineno} {rec_id}: project_training_policy not blocked")
        blob = json.dumps(r)
        for key in ("thought", "chain_of_thought", "inner_monologue", "training_ready"):
            if f'"{key}"' in blob:
                errors.append(f"line {lineno} {rec_id}: forbidden key {key}")
        sim = chosen.get("state", {}).get("sim_or_real") if isinstance(chosen.get("state"), dict) else None
        if sim == "real":
            errors.append(f"line {lineno} {rec_id}: sim_or_real=real")
        delta = r.get("reward_delta")
        if not isinstance(delta, dict) or "total" not in delta:
            errors.append(f"line {lineno} {rec_id}: missing reward_delta")
        print(
            f"pair {rec_id} isolation={iso} "
            f"chosen_decision={sd.get('decision') if isinstance(sd, dict) else None} "
            f"delta_total={delta.get('total') if isinstance(delta, dict) else None}"
        )
    if errors:
        print("purity gate: FAIL", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    print("purity gate: PASS (same-context + no safety-text copy + rights/isolation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
