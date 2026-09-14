#!/usr/bin/env python3
"""Mechanically assemble batch-r12.jsonl. Session B must not read rejected JSON.

Load chosen-0N-r12.json + rejected-0N-r12.json from disk, inject each rejected
scratch verbatim, compute reward_delta as chosen − rejected per numeric head,
and assert chosen.total > rejected.total. Never print rejected JSON.

Pair-level `id` / `goal` / `critique` come from pair-0N-r12.json (preferred)
or from top-level strings on the chosen object. This script does not invent
chosen arms, goals, or critiques.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROUND = 12
ROUND_TAG = f"r{ROUND:02d}"
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
PAIR_COUNT = 3
DEFAULT_STAGE = Path("/tmp/ffpc-r12")

TRAJECTORY_KEYS = (
    "state",
    "proposed_action",
    "safety_decision",
    "executed_action",
    "future_outcome",
    "reward_components",
)

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

FORBIDDEN_KEYS = frozenset(
    {
        "thought",
        "chain_of_thought",
        "scratch",
        "inner_monologue",
        "training_ready",
    }
)

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": GENERATOR,
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
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


def stage_dir() -> Path:
    return Path(os.environ.get("FFPC_STAGE", DEFAULT_STAGE))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> dict:
    data = path.read_bytes()
    return {"name": path.name, "bytes": len(data), "sha256": sha256_bytes(data)}


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def deep_equal(a, b) -> bool:
    # Canonical spelling, not loose numeric equality: 9 != 9.0, True != 1.
    if type(a) is not type(b):
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


def chosen_name(index: int) -> str:
    return f"chosen-{index:02d}-{ROUND_TAG}.json"


def rejected_name(index: int) -> str:
    return f"rejected-{index:02d}-{ROUND_TAG}.json"


def pair_name(index: int) -> str:
    return f"pair-{index:02d}-{ROUND_TAG}.json"


def required_arm_names() -> list[str]:
    names: list[str] = []
    for index in range(1, PAIR_COUNT + 1):
        names.append(chosen_name(index))
        names.append(rejected_name(index))
    return names


def present_regular_file(path: Path) -> bool:
    try:
        return path.is_file() and not path.is_symlink() and path.stat().st_size > 0
    except OSError:
        return False


def inventory(stage: Path) -> dict:
    rows = []
    missing_chosen = []
    missing_rejected = []
    present_chosen = 0
    present_rejected = 0
    for index in range(1, PAIR_COUNT + 1):
        for role, name_fn, missing, counter_attr in (
            ("chosen", chosen_name, missing_chosen, "chosen"),
            ("rejected", rejected_name, missing_rejected, "rejected"),
        ):
            path = stage / name_fn(index)
            if present_regular_file(path):
                digest = file_digest(path)
                rows.append({"role": role, "index": index, **digest, "state": "present"})
                if counter_attr == "chosen":
                    present_chosen += 1
                else:
                    present_rejected += 1
            else:
                rows.append(
                    {
                        "role": role,
                        "index": index,
                        "name": path.name,
                        "bytes": 0,
                        "sha256": None,
                        "state": "missing",
                    }
                )
                missing.append(path.name)
    pair_rows = []
    for index in range(1, PAIR_COUNT + 1):
        path = stage / pair_name(index)
        if present_regular_file(path):
            pair_rows.append({"role": "pair", "index": index, **file_digest(path), "state": "present"})
        else:
            pair_rows.append(
                {
                    "role": "pair",
                    "index": index,
                    "name": path.name,
                    "bytes": 0,
                    "sha256": None,
                    "state": "missing",
                }
            )
    if present_chosen == PAIR_COUNT and present_rejected == PAIR_COUNT:
        state = "READY"
    elif present_rejected == PAIR_COUNT and present_chosen == 0:
        state = "REJECTED_PRESENT_CHOSEN_MISSING"
    elif present_rejected > 0 and present_chosen == 0:
        state = "REJECTED_PARTIAL_CHOSEN_MISSING"
    elif present_chosen == PAIR_COUNT and present_rejected < PAIR_COUNT:
        state = "CHOSEN_PRESENT_REJECTED_MISSING"
    elif present_chosen == 0 and present_rejected == 0:
        state = "EMPTY"
    else:
        state = "PARTIAL"
    return {
        "state": state,
        "present_chosen": present_chosen,
        "present_rejected": present_rejected,
        "missing_chosen": missing_chosen,
        "missing_rejected": missing_rejected,
        "files": rows,
        "pair_sidecars": pair_rows,
    }


def print_status(info: dict) -> None:
    print(f"STATE={info['state']}")
    print(
        f"chosen={info['present_chosen']}/{PAIR_COUNT} "
        f"rejected={info['present_rejected']}/{PAIR_COUNT}"
    )
    if info["missing_chosen"]:
        print("missing_chosen " + " ".join(info["missing_chosen"]))
    if info["missing_rejected"]:
        print("missing_rejected " + " ".join(info["missing_rejected"]))
    for row in info["files"]:
        digest = row["sha256"] or "-"
        print(f"{row['state']} {row['name']} bytes={row['bytes']} sha256={digest}")
    for row in info["pair_sidecars"]:
        digest = row["sha256"] or "-"
        print(f"{row['state']} {row['name']} bytes={row['bytes']} sha256={digest}")
    if info["state"] == "REJECTED_PRESENT_CHOSEN_MISSING":
        print("DO_NOT_INVENT_CHOSEN")
        print("Write chosen-0N-r12.json from diagnosis Shared-context only, then re-run.")


def load_json_object(path: Path, label: str) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"{label}: cannot read {path.name}: {exc}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label}: {path.name} is not JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{label}: {path.name} must be a JSON object")
    return value


def numeric_heads(rc: dict) -> dict:
    heads = {}
    for key, value in rc.items():
        if key in REWARD_SKIP:
            continue
        if is_number(value):
            heads[key] = value
    return heads


def assert_total_reconciles(rc: dict, label: str) -> None:
    if "total" not in rc or not is_number(rc["total"]):
        raise SystemExit(f"{label}: reward_components.total must be a finite number")
    heads = numeric_heads(rc)
    if not heads:
        raise SystemExit(f"{label}: no numeric reward heads")
    summed = float(math.fsum(heads.values()))
    if abs(summed - float(rc["total"])) > 1e-6:
        raise SystemExit(
            f"{label}: reward_components.total {rc['total']} does not equal "
            f"sum of numeric heads {round(summed, 6)}"
        )


def reward_delta(chosen_rc: dict, rejected_rc: dict) -> dict:
    chosen_heads = numeric_heads(chosen_rc)
    rejected_heads = numeric_heads(rejected_rc)
    if set(chosen_heads) != set(rejected_heads):
        delta_keys = sorted(set(chosen_heads) ^ set(rejected_heads))
        raise SystemExit(f"reward head set mismatch: {delta_keys}")
    keys = sorted(chosen_heads)
    per = {key: round(chosen_heads[key] - rejected_heads[key], 6) for key in keys}
    total = round(float(math.fsum(per.values())), 6)
    if abs(total - math.fsum(per.values())) > 1e-6:
        raise SystemExit("reward_delta total does not reconcile")
    if not (chosen_rc["total"] > rejected_rc["total"]):
        raise SystemExit("chosen.total is not greater than rejected.total")
    expected = round(float(chosen_rc["total"]) - float(rejected_rc["total"]), 6)
    if abs(total - expected) > 1e-6:
        raise SystemExit(
            f"reward_delta.total {total} != chosen.total - rejected.total {expected}"
        )
    return {"per_component": per, "total": total}


def collect_forbidden_keys(obj, path: str, out: list[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            if str(key) in FORBIDDEN_KEYS:
                out.append(child)
            collect_forbidden_keys(value, child, out)
        return
    if isinstance(obj, list):
        for i, item in enumerate(obj):
            collect_forbidden_keys(item, f"{path}[{i}]", out)


def assert_no_forbidden(obj: dict, label: str) -> None:
    found: list[str] = []
    collect_forbidden_keys(obj, "", found)
    if found:
        raise SystemExit(f"{label} contains forbidden key(s): {found[:12]}")


def require_trajectory(obj: dict, label: str) -> None:
    missing = [key for key in TRAJECTORY_KEYS if key not in obj]
    if missing:
        raise SystemExit(f"{label}: missing trajectory keys {missing}")
    for key in ("state", "proposed_action", "safety_decision", "executed_action", "future_outcome", "reward_components"):
        if not isinstance(obj.get(key), dict):
            raise SystemExit(f"{label}.{key} must be an object")
    decision = obj["safety_decision"].get("decision")
    if decision not in {"ACCEPT", "MODIFY", "REJECT"}:
        raise SystemExit(f"{label}.safety_decision.decision must be ACCEPT|MODIFY|REJECT")
    sim = obj["state"].get("sim_or_real")
    if sim == "real":
        raise SystemExit(f"{label}: sim_or_real=real")
    if sim not in {"designed", "simulated", "hil"}:
        raise SystemExit(f"{label}: state.sim_or_real must be designed|simulated|hil")
    assert_total_reconciles(obj["reward_components"], f"{label}.reward_components")


def non_empty_string(value) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def default_pair_id(index: int) -> str:
    return f"ffpc-{ROUND_TAG}-{index:03d}"


def pair_id_from_chosen(chosen: dict, index: int) -> str | None:
    raw = non_empty_string(chosen.get("id"))
    if raw is None:
        return None
    suffix = "-chosen"
    if raw.endswith(suffix):
        raw = raw[: -len(suffix)]
    expected = default_pair_id(index)
    if raw == expected:
        return expected
    return raw


def load_pair_sidecar(stage: Path, index: int, chosen: dict) -> dict:
    path = stage / pair_name(index)
    sidecar = {}
    if present_regular_file(path):
        sidecar = load_json_object(path, f"pair {index} sidecar")
        extra = set(sidecar) - {"id", "goal", "critique"}
        if extra:
            raise SystemExit(f"pair {index}: sidecar extra keys {sorted(extra)}")
    pair_id = (
        non_empty_string(sidecar.get("id"))
        or pair_id_from_chosen(chosen, index)
        or default_pair_id(index)
    )
    goal = non_empty_string(sidecar.get("goal")) or non_empty_string(chosen.get("goal"))
    critique = non_empty_string(sidecar.get("critique")) or non_empty_string(
        chosen.get("critique")
    )
    missing = []
    if goal is None:
        missing.append("goal")
    if critique is None:
        missing.append("critique")
    if missing:
        raise SystemExit(
            f"pair {index}: missing {missing}. Write {pair_name(index)} "
            f"from the diagnosis (not rejected JSON) with goal and critique."
        )
    return {"id": pair_id, "goal": goal, "critique": critique}


def strip_pair_fields(chosen: dict) -> dict:
    """Keep the published chosen arm a trajectory, not a preference envelope."""

    cleaned = dict(chosen)
    cleaned.pop("critique", None)
    cleaned.pop("reward_delta", None)
    cleaned.pop("chosen", None)
    cleaned.pop("rejected", None)
    return cleaned


def rights_stamp() -> dict:
    stamp = dict(RIGHTS)
    stamp["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return stamp


def assemble_pair(stage: Path, index: int) -> tuple[dict, dict]:
    chosen_path = stage / chosen_name(index)
    rejected_path = stage / rejected_name(index)
    if not present_regular_file(chosen_path):
        raise SystemExit(f"pair {index}: missing {chosen_path.name} (do not invent chosen)")
    if not present_regular_file(rejected_path):
        raise SystemExit(f"pair {index}: missing {rejected_path.name}")
    chosen_raw = load_json_object(chosen_path, f"pair {index} chosen")
    rejected = load_json_object(rejected_path, f"pair {index} rejected")
    if "chosen" in chosen_raw or "rejected" in chosen_raw:
        raise SystemExit(
            f"pair {index}: {chosen_path.name} looks like a preference envelope; "
            "write a ThalamicTrajectory"
        )
    chosen = strip_pair_fields(chosen_raw)
    require_trajectory(chosen, f"chosen-{index:02d}")
    require_trajectory(rejected, f"rejected-{index:02d}")
    for field in ("state", "proposed_action"):
        if not deep_equal(chosen.get(field), rejected.get(field)):
            paths: list[str] = []
            differing_paths(chosen.get(field), rejected.get(field), field, paths)
            raise SystemExit(
                f"pair {index}: same-context purity failed on {field}; paths={paths[:20]}"
            )
    delta = reward_delta(chosen["reward_components"], rejected["reward_components"])
    pair_meta = load_pair_sidecar(stage, index, chosen_raw)
    record = {
        "id": pair_meta["id"],
        "goal": pair_meta["goal"],
        "chosen": chosen,
        "rejected": rejected,
        "critique": pair_meta["critique"],
        "reward_delta": delta,
        "meta": {
            "round": ROUND,
            "factory": FACTORY,
            "generator": GENERATOR,
            "run_label": RUN_LABEL,
            "isolation": ISOLATION,
            "session": "B",
            "rights": rights_stamp(),
        },
    }
    assert_no_forbidden(record["chosen"], f"chosen-{index:02d}")
    assert_no_forbidden(record["rejected"], f"rejected-{index:02d}")
    assert_no_forbidden({"meta": record["meta"], "id": record["id"]}, f"record-{index:02d}")
    receipt = {
        "id": record["id"],
        "chosen_decision": chosen["safety_decision"]["decision"],
        "chosen_total": chosen["reward_components"]["total"],
        "rejected_total": rejected["reward_components"]["total"],
        "reward_delta_total": delta["total"],
        "reward_delta_per_component": delta["per_component"],
        "chosen": file_digest(chosen_path),
        "rejected": file_digest(rejected_path),
    }
    return record, receipt


def assemble(stage: Path) -> None:
    info = inventory(stage)
    if info["state"] == "REJECTED_PRESENT_CHOSEN_MISSING":
        print_status(info)
        raise SystemExit("rejected scratch is present and chosen is missing; refusing to invent chosen")
    if info["missing_chosen"] or info["missing_rejected"]:
        print_status(info)
        raise SystemExit("arm files missing; not assembling")

    lines = []
    receipt_pairs = []
    for index in range(1, PAIR_COUNT + 1):
        record, receipt = assemble_pair(stage, index)
        lines.append(json.dumps(record, ensure_ascii=True, separators=(",", ":")))
        receipt_pairs.append(receipt)

    batch_path = stage / f"batch-{ROUND_TAG}.jsonl"
    payload = "\n".join(lines) + "\n"
    batch_path.write_text(payload, encoding="utf-8")

    artifacts = [
        stage / chosen_name(i) for i in range(1, PAIR_COUNT + 1)
    ] + [
        stage / "assemble.py",
        stage / f"NOTES-{ROUND_TAG}.md",
        batch_path,
    ]
    artifacts = [path for path in artifacts if path.exists() and path.is_file()]
    receipt = {
        "session": "B",
        "factory": FACTORY,
        "round": ROUND,
        "run_label": RUN_LABEL,
        "generator": GENERATOR,
        "isolation": ISOLATION,
        "linear_issue": "RM-793",
        "intended_use": "research_only",
        "batch": file_digest(batch_path),
        "lines": PAIR_COUNT,
        "artifacts": [file_digest(path) for path in artifacts],
        "pairs": receipt_pairs,
        "note": "rejected JSON was json-loaded at assembly time and not emitted on stdout",
    }
    receipt_path = stage / f"assembler-receipt-{ROUND_TAG}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print("ASSEMBLE_OK")
    print(
        f"batch={batch_path} bytes={receipt['batch']['bytes']} "
        f"sha256={receipt['batch']['sha256']} lines={PAIR_COUNT}"
    )
    for art in receipt["artifacts"]:
        print(f"artifact {art['name']} bytes={art['bytes']} sha256={art['sha256']}")
    for pair in receipt_pairs:
        print(
            f"{pair['id']} decision={pair['chosen_decision']} "
            f"chosen_total={pair['chosen_total']} rejected_total={pair['rejected_total']} "
            f"delta_total={pair['reward_delta_total']}"
        )
    print(f"receipt={receipt_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        default=None,
        help="staging directory (default: $FFPC_STAGE or /tmp/ffpc-r12)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="print file presence/bytes/sha256 only; do not load JSON",
    )
    args = parser.parse_args(argv)
    stage = Path(args.stage) if args.stage else stage_dir()
    if args.status:
        info = inventory(stage)
        print_status(info)
        if info["state"] == "READY":
            return 0
        if info["state"] == "REJECTED_PRESENT_CHOSEN_MISSING":
            return 2
        return 1
    assemble(stage)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(141)
