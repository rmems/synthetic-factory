#!/usr/bin/env python3
"""Read-only operator driver for the synthetic data factory.

Usage:
  driver.py smoke
  driver.py validate <run_dir>
  driver.py audit <run_dir>
  driver.py frontiers <run_dir> [--json]
  driver.py snapshot <run_dir> <label>
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
REPO = SKILL_DIR.parents[2]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from round_txn import frontier_status, publish, reserve  # noqa: E402

VALIDATOR = PIPELINES / "validate_run.py"
CHECKER = PIPELINES / "check_records.py"
AUDITOR = PIPELINES / "training_audit.py"
SAFE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def run_tool(script, run_dir, *options):
    proc = subprocess.run(
        [sys.executable, str(script), *options, str(run_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def snapshot_to_temp(src, prefix):
    temp = tempfile.TemporaryDirectory(prefix=prefix)
    snap = Path(temp.name) / src.name
    shutil.copytree(src, snap)
    return temp, snap


def require_run_dir(run_dir):
    src = Path(run_dir).resolve()
    if not src.is_dir():
        raise SystemExit(f"not a directory: {src}")
    return src


def cmd_validate(run_dir):
    """Shape/invariant validation on a stable copy of a possibly live tree."""
    src = require_run_dir(run_dir)
    temp, snap = snapshot_to_temp(src, "factory-validate-")
    try:
        code, out, err = run_tool(VALIDATOR, snap)
    finally:
        temp.cleanup()
    sys.stdout.write(out)
    sys.stderr.write(err)
    print(
        f"structural validator exit: {code} "
        f"({'CLEAN' if code == 0 else 'DEFECTS FOUND'})"
    )
    return code


def cmd_audit(run_dir):
    """Run all three layers on one stable snapshot; never mutate the source."""
    src = require_run_dir(run_dir)
    temp, snap = snapshot_to_temp(src, "factory-audit-")
    results = []
    try:
        commands = (
            ("STRUCTURAL + SHAPE", VALIDATOR, ()),
            ("DEEP RECORD INVARIANTS", CHECKER, ("--strict",)),
            ("CORPUS TRAINING READINESS", AUDITOR, ("--strict", "--markdown")),
        )
        for title, script, options in commands:
            code, out, err = run_tool(script, snap, *options)
            results.append((title, code, out, err))
    finally:
        temp.cleanup()

    for title, code, out, err in results:
        print(f"\n=== {title} (exit {code}) ===")
        sys.stdout.write(out)
        if err:
            sys.stderr.write(f"\n--- {title} findings ---\n{err}")
    failed = [title for title, code, _out, _err in results if code]
    print(
        "\nAUDIT RESULT: "
        + ("BLOCKED — " + ", ".join(failed) if failed else "TRAINING-READY")
    )
    return 1 if failed else 0


def count_records(factory_dir):
    count = 0
    for path in factory_dir.glob("*.jsonl"):
        try:
            count += count_nonblank_lines(path)
        except OSError:
            continue
    return count


def count_nonblank_lines(path):
    with Path(path).open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def cmd_frontiers(run_dir, as_json=False):
    src = require_run_dir(run_dir)
    factories = []
    for directory in sorted(
        path for path in src.iterdir() if path.is_dir() and not path.name.startswith("_")
    ):
        status = frontier_status(directory)
        status["records"] = count_records(directory)
        factories.append(status)
    payload = {"run_dir": str(src), "factories": factories}
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        for item in factories:
            marker = "committed markers" if item["mode"] == "marker" else "validated legacy"
            print(
                f"{item['factory']}: {item['records']} records, "
                f"highest r{item['highest_flushed']:02d}, "
                f"next r{item['next_round']:02d} ({marker})"
            )
    return factories


def cmd_snapshot(run_dir, label):
    src = require_run_dir(run_dir)
    if not SAFE_LABEL.fullmatch(label):
        raise SystemExit("snapshot label may contain only letters, digits, dot, dash, underscore")
    dst = src.parent / f"{src.name}-{label}"
    if dst.exists():
        raise SystemExit(f"refusing to overwrite existing snapshot: {dst}")
    shutil.copytree(src, dst)
    records = sum(count_nonblank_lines(path) for path in dst.rglob("*.jsonl"))
    print(f"snapshot: {dst} ({records} records)")


def thalamic(record_id="smoke-t1"):
    return {
        "id": record_id,
        "state": {"sim_or_real": "designed", "env": "transaction smoke test"},
        "proposed_action": {"action": "noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "bounded fixture"},
        "executed_action": {"action": "noop"},
        "future_outcome": {"ok": True},
        "reward_components": {"task_progress": 0.5, "total": 0.5},
        "meta": {"factory": "smoke", "round": 2, "tags": ["smoke"]},
    }


MINI_RECORDS = {
    "thalamic-mini/batch-r02.jsonl": [
        thalamic(),
        {
            "id": "smoke-p1",
            "failure_mode": "test",
            "rejected": thalamic("smoke-rejected"),
            "chosen": thalamic("smoke-chosen"),
            "critique": "chosen gate is bounded",
            "reward_delta": {"total": 0.8},
        },
        {
            "id": "smoke-b1",
            "spike_events": [
                {"channel": "c0", "t_rel_ms": 1.0, "amplitude": 0.4},
                {"channel": "c0", "t_rel_ms": 2.0, "amplitude": 0.3},
            ],
            "language_view": {
                "description": "two sparse events",
                "trajectory": thalamic("smoke-bridge-trajectory"),
            },
            "bridge_notes": {"mapping": "fixture", "training_value": "routing"},
        },
        {
            "id": "smoke-e1",
            "goal": "fix fixture",
            "steps": [
                {
                    "n": 1,
                    "decision_basis": "observable file is missing",
                    "tool_call": {"name": "rg", "args": {"q": "fixture"}},
                    "observation": "no match",
                    "reflection": "create bounded fixture",
                }
            ],
            "outcome": "fixed",
            "reward": {"success": True},
        },
    ]
}


def cmd_smoke():
    failures = []
    with tempfile.TemporaryDirectory(prefix="factory-smoke-") as temp_dir:
        root = Path(temp_dir)
        run = root / "mini-run"
        for rel, records in MINI_RECORDS.items():
            path = run / rel
            path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(record) + "\n" for record in records))

        code, out, _err = run_tool(VALIDATOR, run)
        if code:
            failures.append(f"valid mini-run should exit 0, got {code}")
        try:
            totals = json.loads(out)
        except json.JSONDecodeError:
            totals = {}
            failures.append(f"validator emitted invalid JSON totals: {out[:200]!r}")
        expected_kinds = {
            "thalamic": 1,
            "preference": 1,
            "bridge_pair": 1,
            "episode": 1,
        }
        if totals.get("by_kind") != expected_kinds:
            failures.append(f"kind routing wrong: {totals.get('by_kind')}")

        bad = run / "thalamic-mini" / "batch-r03.jsonl"
        broken = thalamic("broken")
        broken["safety_decision"] = {"decision": "MAYBE", "rationale": ""}
        broken["reward_components"] = {}
        bad.write_text(json.dumps(broken) + "\nnot json\n")
        code2, _out2, err2 = run_tool(VALIDATOR, run)
        if code2 == 0:
            failures.append("broken batch should exit nonzero")
        if "decision must be" not in err2 or "JSON parse error" not in err2:
            failures.append(f"expected enum + parse errors, got: {err2[:200]}")
        frontier = cmd_frontiers(run)[0]
        if frontier["next_round"] != 3:
            failures.append(f"malformed r03 must not advance frontier: {frontier}")

        factory = root / "outputs" / "raw" / "2099-01-01" / "thalamic-trajectory-factory"
        factory.mkdir(parents=True)
        reservation = reserve(factory, 1, 1)
        stage = Path(reservation["staging_dir"])
        record = thalamic("txn-smoke")
        record["meta"]["round"] = 1
        (stage / reservation["batch_file"]).write_text(json.dumps(record) + "\n")
        (stage / reservation["notes_file"]).write_text("# Self-critique\n\nFixture only.\n")
        manifest = publish(factory, 1, reservation["token"])
        if manifest.get("records") != 1 or frontier_status(factory)["next_round"] != 2:
            failures.append("transaction reserve/publish did not commit exactly one round")

    if failures:
        print("SMOKE FAIL:")
        for failure in failures:
            print("  -", failure)
        return 1
    print(
        "SMOKE PASS: four record kinds route correctly; malformed output cannot "
        "advance a frontier; reserve/stage/validate/publish commits exactly once"
    )
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        raise SystemExit(__doc__)
    command = args[0]
    if command == "smoke" and len(args) == 1:
        return cmd_smoke()
    if command == "validate" and len(args) == 2:
        return cmd_validate(args[1])
    if command == "audit" and len(args) == 2:
        return cmd_audit(args[1])
    if command == "frontiers" and len(args) >= 2:
        cmd_frontiers(args[1], as_json="--json" in args[2:])
        return 0
    if command == "snapshot" and len(args) == 3:
        cmd_snapshot(args[1], args[2])
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    raise SystemExit(main())
