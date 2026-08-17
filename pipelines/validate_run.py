#!/usr/bin/env python3
"""Validate a dated factory run under outputs/raw/<date>/.

Checks every .jsonl file: each line must parse as JSON, and any embedded
ThalamicTrajectory (top-level, chosen/rejected pair, or language_view.trajectory)
must satisfy schemas/thalamic-trajectory.schema.json's constraints. Coding
episodes are checked against their own shape. Prints totals JSON to stdout
and errors to stderr; exits nonzero if any file has errors. Does not write
manifest.json unless --write is passed.

Usage: python3 pipelines/validate_run.py [--write] <run_dir>
"""

import argparse
import json
import sys
from pathlib import Path

THALAMIC_REQUIRED = [
    "state", "proposed_action", "safety_decision",
    "executed_action", "future_outcome", "reward_components",
]
SAFETY_DECISIONS = {"ACCEPT", "MODIFY", "REJECT"}


def check_thalamic(obj, where):
    errs = []
    for key in THALAMIC_REQUIRED:
        if key not in obj:
            errs.append(f"{where}: missing required key '{key}'")
        elif not isinstance(obj[key], dict):
            errs.append(f"{where}: '{key}' must be an object")
    sd = obj.get("safety_decision")
    if isinstance(sd, dict):
        if sd.get("decision") not in SAFETY_DECISIONS:
            errs.append(f"{where}: safety_decision.decision must be ACCEPT|MODIFY|REJECT")
        rationale = sd.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            errs.append(f"{where}: safety_decision.rationale must be a non-empty string")
    return errs


def check_episode(obj, where):
    errs = []
    for key in ("goal", "steps", "outcome", "reward"):
        if key not in obj:
            errs.append(f"{where}: episode missing '{key}'")
    steps = obj.get("steps")
    if not isinstance(steps, list) or not steps:
        errs.append(f"{where}: steps must be a non-empty array")
    else:
        for i, step in enumerate(steps):
            for key in ("thought", "tool_call", "observation"):
                if key not in step:
                    errs.append(f"{where} step {i}: missing '{key}'")
    return errs


def check_line(obj, where):
    """Route an object to the right checker based on its shape."""
    if not isinstance(obj, dict):
        return [f"{where}: record must be a JSON object"], "unknown"
    if all(k in obj for k in THALAMIC_REQUIRED):
        return check_thalamic(obj, where), "thalamic"
    if "chosen" in obj and "rejected" in obj:
        errs = []
        if not isinstance(obj.get("chosen"), dict):
            errs.append(f"{where}.chosen must be an object")
        else:
            errs += check_thalamic(obj["chosen"], f"{where}.chosen")
        if not isinstance(obj.get("rejected"), dict):
            errs.append(f"{where}.rejected must be an object")
        else:
            errs += check_thalamic(obj["rejected"], f"{where}.rejected")
        if not isinstance(obj.get("critique"), str) or not obj["critique"].strip():
            errs.append(f"{where}: preference record needs a non-empty critique")
        return errs, "preference"
    if "language_view" in obj and "spike_events" in obj:
        errs = []
        events = obj["spike_events"]
        if not isinstance(events, list) or not events:
            errs.append(f"{where}: spike_events must be a non-empty array")
        view = obj.get("language_view")
        if not isinstance(view, dict):
            errs.append(f"{where}: language_view must be an object")
        else:
            traj = view.get("trajectory")
            if isinstance(traj, dict):
                errs += check_thalamic(traj, f"{where}.language_view.trajectory")
            else:
                errs.append(f"{where}: language_view.trajectory missing or not an object")
        return errs, "bridge_pair"
    if "goal" in obj and "steps" in obj:
        return check_episode(obj, where), "episode"
    return [f"{where}: unrecognized record shape (keys: {sorted(obj)[:8]})"], "unknown"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a dated factory run under outputs/raw/<date>/.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write manifest.json into run_dir (default: print totals only)",
    )
    parser.add_argument("run_dir", help="run directory containing .jsonl files")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    manifest = {"run_dir": str(run_dir), "files": [], "totals": {}, "errors": []}
    kind_totals = {}

    for path in sorted(run_dir.rglob("*.jsonl")):
        rel = path.relative_to(run_dir)
        entry = {"file": str(rel), "records": 0, "kinds": {}, "errors": []}
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            where = f"{rel}:{lineno}"
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                entry["errors"].append(f"{where}: JSON parse error: {exc}")
                continue
            errs, kind = check_line(obj, where)
            entry["records"] += 1
            entry["kinds"][kind] = entry["kinds"].get(kind, 0) + 1
            kind_totals[kind] = kind_totals.get(kind, 0) + 1
            entry["errors"].extend(errs)
        manifest["files"].append(entry)
        manifest["errors"].extend(entry["errors"])

    manifest["totals"] = {
        "files": len(manifest["files"]),
        "records": sum(f["records"] for f in manifest["files"]),
        "by_kind": kind_totals,
        "error_count": len(manifest["errors"]),
    }
    if args.write:
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(json.dumps(manifest["totals"], indent=2))
    for err in manifest["errors"]:
        print("ERROR:", err, file=sys.stderr)
    sys.exit(1 if manifest["errors"] else 0)


if __name__ == "__main__":
    main()
