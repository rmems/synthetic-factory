#!/usr/bin/env python3
"""Validate a directory of oracle-grounded records (issue #77).

Fails closed. A record is an error when its envelope is wrong, when its hashes
do not cover what it stores, when its result is missing or not attributed to
the oracle it declares, or when it claims a verdict it does not earn. A record
that honestly reports its own rejection is counted, not treated as an error.

Prints totals JSON on stdout and findings on stderr. Writes nothing.

Usage:
  python3 pipelines/oracle_validate.py [options] <run_dir>

Options:
  --family NAME       Only validate this family (repeatable).
  --require-runtime   Treat reference-oracle records as errors.
  --reproduce         Re-run each oracle and compare the measurement hash.
  --max-findings N    Stop printing findings after N lines (default 50).
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from oracle_grounded import families, record


def parse_args(argv):
    parser = argparse.ArgumentParser(add_help=True, description=__doc__)
    parser.add_argument("run_dir", nargs="?")
    parser.add_argument("--family", action="append", dest="family_names")
    parser.add_argument("--require-runtime", action="store_true")
    parser.add_argument("--reproduce", action="store_true")
    parser.add_argument("--max-findings", type=int, default=50)
    return parser.parse_args(argv)


def validate_file(path, require_runtime, reproduce, selected):
    """Validate one JSONL file. Returns (totals, errors)."""
    totals = Counter()
    errors = []
    text = path.read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        where = f"{path}:{number}"
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            totals["parse_failures"] += 1
            errors.append(f"{where}: JSON parse error: {exc}")
            continue
        if not isinstance(item, dict):
            totals["parse_failures"] += 1
            errors.append(f"{where}: record is not a JSON object")
            continue
        family = item.get("family")
        if selected and family not in selected:
            totals["skipped"] += 1
            continue
        totals["records"] += 1

        layers = record.classify(item, require_named_runtime=require_runtime)
        fatal = layers["envelope"] + layers["status"]
        if fatal:
            totals["invalid"] += 1
            for finding in fatal:
                errors.append(f"{where}: {finding}")
            continue
        if layers["family"]:
            totals["rejected"] += 1
        else:
            totals["accepted"] += 1
        if item["oracle"]["implementation"] == "reference":
            totals["reference_oracle"] += 1
        else:
            totals["named_runtime"] += 1
        if item["validation"].get("publishable"):
            totals["publishable"] += 1

        if reproduce:
            status, detail = record.reproduce(item)
            totals[f"reproduce_{status}"] += 1
            if status == "mismatch":
                totals["invalid"] += 1
                errors.append(f"{where}: oracle result did not reproduce: {detail}")
    return totals, errors


def validate_run(run_dir, require_runtime=False, reproduce=False, selected=()):
    totals = Counter()
    errors = []
    by_family = Counter()
    files = 0
    for path in sorted(Path(run_dir).rglob("*.jsonl")):
        files += 1
        file_totals, file_errors = validate_file(path, require_runtime, reproduce, selected)
        totals.update(file_totals)
        errors.extend(file_errors)
        if file_totals["records"]:
            # Skip zero entries so a --family filter reports only what it kept.
            by_family[path.parent.name] += file_totals["records"]
    report = {
        "run_dir": str(Path(run_dir).resolve()),
        "files": files,
        "records": totals["records"],
        "accepted": totals["accepted"],
        "rejected": totals["rejected"],
        "invalid": totals["invalid"],
        "parse_failures": totals["parse_failures"],
        "skipped": totals["skipped"],
        "reference_oracle": totals["reference_oracle"],
        "named_runtime": totals["named_runtime"],
        "publishable": totals["publishable"],
        "by_family": dict(sorted(by_family.items())),
    }
    if reproduce:
        report["reproduce"] = {
            key.removeprefix("reproduce_"): value
            for key, value in sorted(totals.items())
            if key.startswith("reproduce_")
        }
    return report, errors


def main(argv=None):
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if not args.run_dir:
        print("oracle_validate: a run directory is required", file=sys.stderr)
        return 2
    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"oracle_validate: not a directory: {run_dir}", file=sys.stderr)
        return 2
    selected = set(args.family_names or ())
    unknown = sorted(selected - set(families.SPECS))
    if unknown:
        print(f"oracle_validate: unknown families: {', '.join(unknown)}", file=sys.stderr)
        return 2

    report, errors = validate_run(
        run_dir,
        require_runtime=args.require_runtime,
        reproduce=args.reproduce,
        selected=selected,
    )
    print(json.dumps(report, indent=2))
    for finding in errors[: max(0, args.max_findings)]:
        print(finding, file=sys.stderr)
    if len(errors) > args.max_findings:
        print(f"... {len(errors) - args.max_findings} more findings", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
