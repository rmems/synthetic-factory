#!/usr/bin/env python3
"""Generate oracle-grounded neuromorphic records (issue #77).

For each dataset family the generator proposes scenarios and interventions and
the family's oracle adapter measures the outcome. Accepted and rejected records
are written to separate files so curation is fail-closed by construction: a
consumer that reads only `accepted-*.jsonl` never sees a record whose oracle
result is missing, unattributed, or failing its family's invariants.

Nothing is overwritten. A run whose output files already exist exits nonzero.

Usage:
  python3 pipelines/oracle_generate.py [options] <out_dir>

Options:
  --family NAME         Restrict to one family (repeatable). Default: all five.
  --count N             Proposals per family (default 8).
  --seed N              Master seed (default 20260823).
  --round N             Round number stamped into ids and filenames (default 1).
  --oracle-commit SHA   Pin the commit stamped into records instead of asking git.
  --oracle-dirty        Force the recorded dirty flag on.
  --no-oracle-dirty     Force the recorded dirty flag off.
  --require-runtime     Refuse to write unless every named runtime is bound.
  --list-families       Print the family names and exit.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from oracle_grounded import canon, families, oracles, record

DEFAULT_SEED = 20260823
DEFAULT_COUNT = 8


def parse_args(argv):
    parser = argparse.ArgumentParser(add_help=True, description=__doc__)
    parser.add_argument("out_dir", nargs="?")
    parser.add_argument("--family", action="append", dest="family_names")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--round", type=int, default=1, dest="round_number")
    parser.add_argument("--oracle-commit", dest="oracle_commit")
    parser.add_argument(
        "--oracle-dirty", dest="oracle_dirty", action="store_true", default=None
    )
    parser.add_argument("--no-oracle-dirty", dest="oracle_dirty", action="store_false")
    parser.add_argument("--require-runtime", action="store_true")
    parser.add_argument("--list-families", action="store_true")
    return parser.parse_args(argv)


def generate_family(family, count, seed, round_number, commit, dirty, require_runtime):
    """Build ``count`` records for one family, split by verdict."""
    accepted = []
    rejected = []
    errors = []
    for index in range(count):
        try:
            item = record.build_record(
                family,
                index,
                seed=seed,
                round_number=round_number,
                commit=commit,
                dirty=dirty,
            )
        except (oracles.OracleError, record.GenerationError) as exc:
            errors.append(f"{family}#{index}: {type(exc).__name__}: {exc}")
            continue
        findings = record.validate_record(
            item, require_named_runtime=require_runtime
        )
        if item["validation"]["status"] == "accepted" and not findings:
            accepted.append(item)
        else:
            rejected.append(item)
    return accepted, rejected, errors


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(canon.dumps_record(item) + "\n" for item in records)
    path.write_text(body, encoding="utf-8")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def summarize(records):
    scored = [
        item["validation"]["candidate_prediction_correct"]
        for item in records
        if item["validation"]["candidate_prediction_correct"] is not None
    ]
    return {
        "records": len(records),
        "candidate_scored": len(scored),
        "candidate_correct": sum(1 for value in scored if value),
    }


def main(argv=None):
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.list_families:
        for name in families.FAMILY_NAMES:
            print(name)
        return 0
    if not args.out_dir:
        print("oracle_generate: an output directory is required", file=sys.stderr)
        return 2
    if args.count < 1:
        print("oracle_generate: --count must be at least 1", file=sys.stderr)
        return 2
    if args.round_number < 1:
        print("oracle_generate: --round must be at least 1", file=sys.stderr)
        return 2

    selected = args.family_names or list(families.FAMILY_NAMES)
    unknown = [name for name in selected if name not in families.SPECS]
    if unknown:
        print(f"oracle_generate: unknown families: {', '.join(unknown)}", file=sys.stderr)
        return 2

    selected_runtimes = tuple(
        dict.fromkeys(
            runtime
            for family in selected
            for runtime in families.spec_for(family).runtimes
        )
    )
    availability = oracles.availability_report(selected_runtimes)
    if args.require_runtime and not availability["all_bound"]:
        print(
            "oracle_generate: --require-runtime was passed but these oracles are "
            f"not bound: {', '.join(availability['unbound'])}",
            file=sys.stderr,
        )
        return 3

    commit, dirty = args.oracle_commit, args.oracle_dirty
    if commit is None:
        commit, resolved_dirty = oracles.resolve_commit()
        if dirty is None:
            dirty = resolved_dirty
    if commit == "unknown":
        print(
            "oracle_generate: could not resolve the oracle commit; pass "
            "--oracle-commit to stamp it explicitly",
            file=sys.stderr,
        )
        return 3

    out_dir = Path(args.out_dir)
    targets = {}
    for family in selected:
        for verdict in ("accepted", "rejected"):
            targets[(family, verdict)] = (
                out_dir / family / f"{verdict}-r{args.round_number:02d}.jsonl"
            )
    existing = [str(path) for path in targets.values() if path.exists()]
    manifest_path = out_dir / "manifest.json"
    if manifest_path.exists():
        existing.append(str(manifest_path))
    if existing:
        print(
            "oracle_generate: refusing to overwrite: " + ", ".join(sorted(existing)),
            file=sys.stderr,
        )
        return 2

    per_family = {}
    files = {}
    all_errors = []
    for family in selected:
        accepted, rejected, errors = generate_family(
            family,
            args.count,
            args.seed,
            args.round_number,
            commit,
            dirty,
            args.require_runtime,
        )
        all_errors.extend(errors)
        for verdict, items in (("accepted", accepted), ("rejected", rejected)):
            path = targets[(family, verdict)]
            digest = write_jsonl(path, items)
            files[str(path.relative_to(out_dir))] = {
                "sha256": digest,
                "records": len(items),
            }
        per_family[family] = {
            "proposed": args.count,
            "accepted": summarize(accepted),
            "rejected": {
                "records": len(rejected),
                "reasons": sorted(
                    {reason for item in rejected for reason in item["validation"]["reasons"]}
                ),
            },
            "oracle": {
                "requested_runtime": list(families.spec_for(family).runtimes),
                "implementation": (
                    accepted[0]["oracle"]["implementation"]
                    if accepted
                    else (rejected[0]["oracle"]["implementation"] if rejected else None)
                ),
            },
        }

    manifest = {
        "schema": record.SCHEMA_ID,
        "round": args.round_number,
        "seed": args.seed,
        "count_per_family": args.count,
        "families": per_family,
        "oracle_commit": commit,
        "oracle_dirty": dirty,
        "module_digest": oracles.module_digest(),
        "oracle_availability": availability,
        "files": files,
        "generation_errors": all_errors,
        "note": (
            "Counts describe this run only. A reference-implementation oracle "
            "measures a real model but is not the named runtime; no record here "
            "is publishable as a measurement of the named runtime."
        ),
    }
    manifest_path.write_text(
        json.dumps(canon.normalize(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(canon.normalize(manifest), indent=2, sort_keys=True))
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
