#!/usr/bin/env python3
"""Allocate the next unused factory round.

Scans batch-rNN.jsonl, NOTES-rNN.md, unmarked round-1 jsonl names, and any
jsonl meta.round integers. next_round is max(found)+1 (or 1 if none).

Refuses (exit 1) if the target batch-rNN.jsonl already exists. Does not write
trajectory files. --write-index may write NEXT_ROUND.json only.

Usage:
  python3 pipelines/next_round.py <factory_dir>
  python3 pipelines/next_round.py --allocate N <factory_dir>
  python3 pipelines/next_round.py --write-index <run_root>
"""

import argparse
import json
import re
import sys
from pathlib import Path

BATCH_RE = re.compile(r"^batch-r(\d+)\.jsonl$")
NOTES_RE = re.compile(r"^NOTES-r(\d+)\.md$")
ROUND1_FILENAMES = frozenset(
    {
        "trajectories.jsonl",
        "pairs.jsonl",
        "preferences.jsonl",
        "episodes.jsonl",
        "final-trajectories.jsonl",
    }
)


class RoundExistsError(FileExistsError):
    """Suggested batch-rNN.jsonl is already on disk."""


def batch_filename(n):
    return f"batch-r{n:02d}.jsonl"


def notes_filename(n):
    return f"NOTES-r{n:02d}.md"


def _as_round(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _meta_rounds(obj, found):
    if isinstance(obj, dict):
        meta = obj.get("meta")
        if isinstance(meta, dict):
            n = _as_round(meta.get("round"))
            if n is not None:
                found.add(n)
        for value in obj.values():
            _meta_rounds(value, found)
    elif isinstance(obj, list):
        for item in obj:
            _meta_rounds(item, found)


def _rounds_from_jsonl(path):
    found = set()
    try:
        text = path.read_text()
    except OSError:
        return found
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        _meta_rounds(obj, found)
    return found


def scan_rounds(factory_dir):
    """Return the set of round integers found in a factory directory."""
    factory_dir = Path(factory_dir)
    found = set()
    if not factory_dir.is_dir():
        return found
    for path in factory_dir.iterdir():
        if not path.is_file():
            continue
        match = BATCH_RE.fullmatch(path.name)
        if match:
            found.add(int(match.group(1)))
        match = NOTES_RE.fullmatch(path.name)
        if match:
            found.add(int(match.group(1)))
        if path.name in ROUND1_FILENAMES:
            found.add(1)
        if path.suffix == ".jsonl":
            found |= _rounds_from_jsonl(path)
    return found


def factory_plan(factory_dir, n=None):
    factory_dir = Path(factory_dir)
    existing = sorted(scan_rounds(factory_dir))
    if n is None:
        n = existing[-1] + 1 if existing else 1
    return {
        "factory": factory_dir.name,
        "next_round": n,
        "write": batch_filename(n),
        "notes": notes_filename(n),
        "existing": existing,
    }


def allocate(factory_dir, n=None):
    """Return a plan for round n (or next unused). Refuse if batch-rNN exists."""
    factory_dir = Path(factory_dir)
    plan = factory_plan(factory_dir, n)
    n = plan["next_round"]
    collisions = [
        path.name
        for path in factory_dir.glob("batch-r*.jsonl")
        if BATCH_RE.fullmatch(path.name) and int(BATCH_RE.fullmatch(path.name).group(1)) == n
    ]
    if collisions:
        raise RoundExistsError(f"refuse: {collisions[0]} already exists")
    return plan


def is_factory_dir(path):
    path = Path(path)
    if not path.is_dir() or path.name.startswith("."):
        return False
    for child in path.iterdir():
        if not child.is_file():
            continue
        if child.suffix == ".jsonl" or child.name.startswith("NOTES"):
            return True
    return False


def write_index(run_root):
    """Write run_root/NEXT_ROUND.json. Never writes trajectory files."""
    run_root = Path(run_root)
    entries = []
    if run_root.is_dir():
        for child in sorted(run_root.iterdir(), key=lambda p: p.name):
            if is_factory_dir(child):
                entries.append(factory_plan(child))
    payload = {
        "run_root": str(run_root.resolve()),
        "factories": entries,
    }
    out = run_root / "NEXT_ROUND.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")
    return payload, out


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Allocate the next unused factory round.",
    )
    parser.add_argument(
        "--write-index",
        action="store_true",
        help="write NEXT_ROUND.json under run_root (not trajectory data)",
    )
    parser.add_argument(
        "--allocate",
        type=int,
        metavar="N",
        help="claim round N; exit 1 if batch-rNN.jsonl already exists",
    )
    parser.add_argument(
        "path",
        help="factory directory, or run root with --write-index",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    path = Path(args.path)
    if args.write_index:
        if args.allocate is not None:
            print("refuse: --write-index cannot be combined with --allocate", file=sys.stderr)
            sys.exit(2)
        if not path.is_dir():
            print(f"error: not a directory: {path}", file=sys.stderr)
            sys.exit(2)
        payload, _out = write_index(path)
        print(json.dumps(payload, indent=2))
        sys.exit(0)

    if not path.is_dir():
        print(f"error: not a directory: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        plan = allocate(path, args.allocate)
    except RoundExistsError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(plan))
    sys.exit(0)


if __name__ == "__main__":
    main()
