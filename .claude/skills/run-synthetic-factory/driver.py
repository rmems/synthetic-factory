#!/usr/bin/env python3
"""Driver for the synthetic-factory: validate runs, compute frontiers, snapshot.

Stdlib only. All commands are read-only on the run tree except `snapshot`
(which only creates a new sibling directory).

Usage:
  driver.py smoke                        self-test the validator on a generated mini-run
  driver.py validate <run_dir>           snapshot-validate a (possibly live) run tree
  driver.py frontiers <run_dir> [--json] per-factory highest flushed round + next round
  driver.py snapshot <run_dir> <label>   durable copy to <run_dir>-<label> (refuses to clobber)
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
REPO = SKILL_DIR.parents[2]
VALIDATOR = REPO / "pipelines" / "validate_run.py"


def run_validator(run_dir):
    """Run the repo validator; return (exit_code, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(run_dir)],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def cmd_validate(run_dir):
    """Copy the tree first so validating a live, mid-write run is safe."""
    src = Path(run_dir).resolve()
    if not src.is_dir():
        sys.exit(f"not a directory: {src}")
    with tempfile.TemporaryDirectory(prefix="factory-validate-") as tmp:
        snap = Path(tmp) / src.name
        shutil.copytree(src, snap)
        code, out, err = run_validator(snap)
    sys.stdout.write(out)
    sys.stderr.write(err)
    print(f"validator exit: {code} ({'CLEAN' if code == 0 else 'ERRORS'})")
    return code


def cmd_frontiers(run_dir, as_json=False):
    src = Path(run_dir).resolve()
    factories = []
    for d in sorted(p for p in src.iterdir() if p.is_dir() and not p.name.startswith("_")):
        rounds = sorted({
            int(m.group(1))
            for f in d.iterdir()
            if (m := re.match(r"batch-r(\d+)", f.name))
        })
        # round 1 files use fixed names (trajectories/pairs/preferences/episodes/final-*)
        has_r01 = any(f.suffix == ".jsonl" and not f.name.startswith("batch-") for f in d.iterdir())
        highest = max(rounds) if rounds else (1 if has_r01 else 0)
        factories.append({
            "factory": d.name,
            "highest_flushed": highest,
            "next_round": highest + 1,
            "records": sum(
                sum(1 for line in f.open() if line.strip())
                for f in d.glob("*.jsonl")
            ),
        })
    if as_json:
        print(json.dumps({"run_dir": str(src), "factories": factories}, indent=2))
    else:
        for f in factories:
            print(f"{f['factory']}: {f['records']} records, "
                  f"highest r{f['highest_flushed']:02d}, next r{f['next_round']:02d}")
    return factories


def cmd_snapshot(run_dir, label):
    src = Path(run_dir).resolve()
    dst = src.parent / f"{src.name}-{label}"
    if dst.exists():
        sys.exit(f"refusing to overwrite existing snapshot: {dst}")
    shutil.copytree(src, dst)
    n = sum(1 for p in dst.rglob("*.jsonl") for line in p.open() if line.strip())
    print(f"snapshot: {dst} ({n} records)")


MINI_RECORDS = {
    "thalamic-mini/batch-r02.jsonl": [
        {"state": {"env": "test"}, "proposed_action": {"a": 1},
         "safety_decision": {"decision": "MODIFY", "rationale": "clamp force"},
         "executed_action": {"a": 1}, "future_outcome": {"ok": True},
         "reward_components": {"task_progress": 0.5, "total": 0.5},
         "meta": {"factory": "smoke", "round": 2}},
        {"failure_mode": "test",
         "rejected": {"state": {}, "proposed_action": {},
                      "safety_decision": {"decision": "ACCEPT", "rationale": "x"},
                      "executed_action": {}, "future_outcome": {},
                      "reward_components": {"total": 0.1}},
         "chosen": {"state": {}, "proposed_action": {},
                    "safety_decision": {"decision": "REJECT", "rationale": "y"},
                    "executed_action": {}, "future_outcome": {},
                    "reward_components": {"total": 0.9}},
         "critique": "chosen gates correctly", "reward_delta": {"total": 0.8}},
        {"spike_events": [{"channel": "c0", "t_rel_ms": 1.0, "amplitude": 0.4}],
         "language_view": {"description": "one spike",
                           "trajectory": {"state": {}, "proposed_action": {},
                                          "safety_decision": {"decision": "ACCEPT", "rationale": "z"},
                                          "executed_action": {}, "future_outcome": {},
                                          "reward_components": {"total": 0.7}}},
         "bridge_notes": {"mapping": "m", "training_value": "v"}},
        {"goal": "fix bug", "steps": [{"n": 1, "thought": "look", "tool_call":
         {"name": "grep", "args": {"q": "x"}}, "observation": "found", "reflection": "ok"}],
         "outcome": "fixed", "reward": {"success": True}},
    ],
}


def cmd_smoke():
    failures = []
    with tempfile.TemporaryDirectory(prefix="factory-smoke-") as tmp:
        run = Path(tmp) / "mini-run"
        for rel, records in MINI_RECORDS.items():
            f = run / rel
            f.parent.mkdir(parents=True)
            f.write_text("".join(json.dumps(r) + "\n" for r in records))

        code, out, _ = run_validator(run)
        totals = json.loads(out)
        if code != 0:
            failures.append(f"valid mini-run should exit 0, got {code}")
        if totals["by_kind"] != {"thalamic": 1, "preference": 1, "bridge_pair": 1, "episode": 1}:
            failures.append(f"kind routing wrong: {totals['by_kind']}")

        bad = run / "thalamic-mini" / "batch-r03.jsonl"
        bad.write_text(json.dumps({"state": {}, "proposed_action": {},
                                   "safety_decision": {"decision": "MAYBE", "rationale": ""},
                                   "executed_action": {}, "future_outcome": {},
                                   "reward_components": {}}) + "\nnot json\n")
        code2, _, err2 = run_validator(run)
        if code2 == 0:
            failures.append("broken batch should exit nonzero")
        if "decision must be" not in err2 or "JSON parse error" not in err2:
            failures.append(f"expected enum + parse errors, got: {err2[:200]}")

        fr = cmd_frontiers(run, as_json=False)
        if fr[0]["next_round"] != 4:
            failures.append(f"frontier should be next r04, got {fr[0]}")

    if failures:
        print("SMOKE FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("SMOKE PASS: validator accepts all 4 record kinds, rejects enum/parse "
          "violations, frontier detection correct")


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    cmd = args[0]
    if cmd == "smoke":
        cmd_smoke()
    elif cmd == "validate" and len(args) >= 2:
        sys.exit(cmd_validate(args[1]))
    elif cmd == "frontiers" and len(args) >= 2:
        cmd_frontiers(args[1], as_json="--json" in args)
    elif cmd == "snapshot" and len(args) >= 3:
        cmd_snapshot(args[1], args[2])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
