#!/usr/bin/env python3
"""Execution-grounded verification for synthetic-factory records.

Distinguishes verified / inconclusive / failed. Never treats
`cannot-verify` as `verified` (Ouroboros #1991, Codex #37278).

Frontier gate integration:
  pipelines/round_txn.py owns the frontier commit point
  (ROUND-rNN.complete.json). Execution verification is a live co-gate:
  round_txn.validate_stage() calls verify_batch_for_frontier(strict=True)
  through round_txn.execution_gate() and refuses to publish while any
  record is failed or inconclusive. round_txn remains the commit-point
  owner; verify_execution remains the source of truth for
  verified / inconclusive / failed. See docs/verify-execution.md.

Usage:
  python3 pipelines/verify_execution.py <run_dir> [--strict]
  python3 pipelines/verify_execution.py --record <jsonl> --line N
  # frontier gate (import hook, no CLI coupling):
  #   from verify_execution import verify_batch_for_frontier
  #   counts, findings, blocked = verify_batch_for_frontier(batch_path, strict=True)

Co-authored-by: Muse Code powered by Muse Spark <muse-spark@meta.com>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Reuse the existing validator vocabulary as ground truth.
try:
    from check_records import ALLOWED_SIM_OR_REAL
except ImportError:  # pragma: no cover - depends on sys.path of the caller
    print(
        "verify_execution: check_records unavailable — falling back to the "
        "built-in state.sim_or_real set",
        file=sys.stderr,
    )
    ALLOWED_SIM_OR_REAL = frozenset({"designed", "simulated", "hil"})

try:
    from validate_run import (
        THALAMIC_CORE_KEYS,
        check_episode,
        check_line,
        check_safety_case,
    )
except ImportError:  # pragma: no cover - publish imports from the repo tree
    THALAMIC_CORE_KEYS = (
        "state",
        "proposed_action",
        "safety_decision",
        "executed_action",
        "future_outcome",
        "reward_components",
    )
    check_episode = None
    check_line = None
    check_safety_case = None


from verify_execution_shapes import (  # noqa: E402
    verify_record_execution,
)

# ---------------------------------------------------------------------------
# Frontier gate — integration with pipelines/round_txn.py
# ---------------------------------------------------------------------------
# pipelines/round_txn.py:validate_stage() is the training-ready gate that
# runs check_jsonl() and quota checks before publish() links
# ROUND-rNN.complete.json. Execution verification is a live co-gate there:
# a round must not become visible to frontier readers when its records lack
# observable execution evidence.
#
# Live call site (pipelines/round_txn.py:execution_gate, invoked from
# validate_stage() after the envelope check):
#
#   verify_batch_for_frontier = load_execution_verifier()
#   counts, findings, blocked = verify_batch_for_frontier(batch, strict=True)
#   # failed        -> TransactionError, never waivable
#   # inconclusive  -> TransactionError unless the operator passed
#   #                  --allow-inconclusive "<reason>", which is recorded in
#   #                  ROUND-rNN.complete.json
#
# publish() links ROUND-rNN.complete.json only if both gates pass, so an
# unverifiable round cannot advance frontier_status().next_round.
#
# This keeps a clean separation: round_txn owns the atomic commit point
# and filesystem invariants; verify_execution owns the verified /
# inconclusive / failed taxonomy and never promotes cannot-verify.
# The import is on-demand so verify_execution can audit any run_dir without a
# round_txn reservation — but a missing verifier fails the publish closed
# rather than skipping the gate.
#
# See docs/verify-execution.md for the full contract, strict vs non-strict
# semantics, the waiver format, and the test matrix.
# ---------------------------------------------------------------------------


def jsonl_lines(text):
    """Split JSONL on literal LF only.

    ``str.splitlines()`` also splits at U+2028/U+2029, which remain ordinary
    JSON string data and must not become record boundaries. Staging validation
    (`check_jsonl`) uses the same literal-LF contract.
    """
    return text.split("\n")


def verify_batch_for_frontier(batch_path: Path, strict: bool = False):
    """Verify a single staged batch file for frontier gating.

    This is the primary hook consumed by pipelines/round_txn.py.
    It mirrors audit_run() but scoped to one batch file so
    validate_stage() can gate before linking ROUND-rNN.complete.json.

    Args:
        batch_path: path to batch-rNN.jsonl (staged or committed).
        strict: when True, inconclusive also blocks the frontier;
                when False (default), only failed blocks.

    Returns:
        (counts, findings, blocked) where blocked is the frontier-gate
        decision. Findings are a list of {file, line, status, reason}.

    Frontier gate semantics:
        blocked = (failed > 0) or (strict and inconclusive > 0)
        — never promote cannot-verify to verified.
    """
    batch_path = Path(batch_path)
    counts = {"verified": 0, "inconclusive": 0, "failed": 0, "total": 0}
    findings: list[dict] = []
    try:
        lines = jsonl_lines(batch_path.read_text())
    except (OSError, UnicodeError) as exc:
        findings.append({"file": str(batch_path), "line": 0, "status": "failed", "reason": str(exc)})
        counts["failed"] = 1
        counts["total"] = 1
        return counts, findings, True

    for lineno, line in enumerate(lines, 1):
        if not line.strip():
            continue
        where = f"{batch_path.name}:{lineno}"
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            counts["failed"] += 1
            counts["total"] += 1
            findings.append({"file": str(batch_path), "line": lineno, "status": "failed", "reason": f"JSON parse: {exc}"})
            continue
        status, reason = verify_record_execution(obj, where)
        counts[status] += 1
        counts["total"] += 1
        if status != "verified":
            findings.append({"file": str(batch_path), "line": lineno, "status": status, "reason": reason})

    blocked = counts["failed"] > 0 or (strict and counts["inconclusive"] > 0)
    return counts, findings, blocked


def verify_stage_for_frontier(stage_dir: Path, round_number: int, strict: bool = False):
    """Verify the staged batch inside a round_txn staging directory.

    Convenience wrapper around verify_batch_for_frontier() that resolves
    stage_dir / batch-rNN.jsonl via round_txn staging conventions.

    Intended call site (comment hook):
        # pipelines/round_txn.py:validate_stage()
        # from verify_execution import verify_stage_for_frontier
        # counts, findings, blocked = verify_stage_for_frontier(stage, round_number, strict=True)
    """
    stage_dir = Path(stage_dir)
    batch = stage_dir / f"batch-r{round_number:02d}.jsonl"
    return verify_batch_for_frontier(batch, strict=strict)


def frontier_gate_result(batch_path: Path, strict: bool = False) -> dict:
    """Return a JSON-serializable frontier gate verdict for a batch.

    Small helper for round_txn error messages and for docs/verify-execution.md
    examples. Does not raise; the caller decides whether to raise
    TransactionError.
    """
    counts, findings, blocked = verify_batch_for_frontier(batch_path, strict=strict)
    return {
        "batch": str(batch_path),
        "strict": strict,
        "counts": counts,
        "findings": findings,
        "blocked": blocked,
        "gate": "pipelines/verify_execution.py:verify_batch_for_frontier -> pipelines/round_txn.py:validate_stage",
    }


def audit_run(run_dir: Path, strict: bool = False):
    run_dir = Path(run_dir)
    counts = {"verified": 0, "inconclusive": 0, "failed": 0, "total": 0}
    findings = []
    for path in sorted(run_dir.rglob("*.jsonl")):
        rel = path.relative_to(run_dir)
        try:
            lines = jsonl_lines(path.read_text())
        except OSError as e:
            findings.append({"file": str(rel), "line": 0, "status": "failed", "reason": str(e)})
            continue
        for lineno, line in enumerate(lines, 1):
            if not line.strip():
                continue
            where = f"{rel}:{lineno}"
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                counts["failed"] += 1
                counts["total"] += 1
                findings.append({"file": str(rel), "line": lineno, "status": "failed", "reason": f"JSON parse: {e}"})
                continue
            status, reason = verify_record_execution(obj, where)
            counts[status] += 1
            counts["total"] += 1
            if status != "verified":
                findings.append({"file": str(rel), "line": lineno, "status": status, "reason": reason})
    # Gate: strict blocks on any inconclusive; non-strict only blocks on failed
    blocked = counts["failed"] > 0 or (strict and counts["inconclusive"] > 0)
    return counts, findings, blocked


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Execution-grounded verification (verified/inconclusive/failed)")
    p.add_argument("run_dir", nargs="?", help="run directory containing .jsonl files")
    p.add_argument("--strict", action="store_true", help="inconclusive also blocks (default: only failed blocks)")
    p.add_argument("--record", help="single jsonl file to check")
    p.add_argument("--line", type=int, help="line number for --record mode")
    p.add_argument("--json", action="store_true", help="emit JSON findings")
    p.add_argument("--batch", help="single batch file for frontier gate check (alias for --record dir batch)")
    args = p.parse_args(argv)

    if args.record:
        path = Path(args.record)
        lineno = 1 if args.line is None else args.line
        try:
            text = jsonl_lines(path.read_text())
        except OSError as exc:
            print(json.dumps({"status": "failed", "reason": str(exc)}, indent=2))
            sys.exit(1)
        if lineno < 1 or lineno > len(text):
            print(json.dumps({
                "status": "failed",
                "reason": f"--line {lineno} out of range (file has {len(text)} lines)",
            }, indent=2))
            sys.exit(1)
        try:
            obj = json.loads(text[lineno - 1])
        except json.JSONDecodeError as exc:
            print(json.dumps({"status": "failed", "reason": f"JSON parse: {exc}"}, indent=2))
            sys.exit(1)
        status, reason = verify_record_execution(obj, f"{path}:{lineno}")
        print(json.dumps({"status": status, "reason": reason}, indent=2))
        sys.exit(0 if status == "verified" else 1)

    if args.batch:
        counts, findings, blocked = verify_batch_for_frontier(Path(args.batch), strict=args.strict)
        if args.json:
            print(json.dumps({"counts": counts, "findings": findings, "blocked": blocked}, indent=2))
        else:
            print(json.dumps(counts, indent=2))
            for f in findings:
                print(f"{f['status'].upper()}: {f['file']}:{f['line']} — {f['reason']}", file=sys.stderr)
        sys.exit(1 if blocked else 0)

    if not args.run_dir:
        p.print_help()
        sys.exit(2)
    counts, findings, blocked = audit_run(Path(args.run_dir), strict=args.strict)
    if args.json:
        print(json.dumps({"counts": counts, "findings": findings, "blocked": blocked}, indent=2))
    else:
        print(json.dumps(counts, indent=2))
        for f in findings:
            print(f"{f['status'].upper()}: {f['file']}:{f['line']} — {f['reason']}", file=sys.stderr)
    sys.exit(1 if blocked else 0)


if __name__ == "__main__":
    main()
