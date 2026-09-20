"""Run a deterministic round-robin shard of the unittest modules."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def discover_modules(root: Path = ROOT) -> list[str]:
    """Return sorted test module stems discovered directly under ``tests``."""
    return sorted(path.stem for path in (root / "tests").glob("test_*.py"))


def shard_modules(modules: list[str], shard: int, shards: int) -> list[str]:
    """Select one deterministic round-robin shard from ``modules``."""
    return [module for index, module in enumerate(modules) if index % shards == shard]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, required=True)
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--list", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run or list the selected unittest shard."""
    parser = _parser()
    args = parser.parse_args(argv)
    if args.shards < 1 or not 0 <= args.shard < args.shards:
        parser.error("--shard must satisfy 0 <= shard < shards, with shards >= 1")

    chosen = shard_modules(discover_modules(), args.shard, args.shards)
    if args.list:
        print("\n".join(chosen))
        return 0

    command = [sys.executable]
    if args.coverage:
        command.extend(["-m", "coverage", "run", "-p"])
    command.extend(["-m", "unittest", "-b", *chosen])
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(ROOT / "tests")
    if existing_pythonpath:
        environment["PYTHONPATH"] += os.pathsep + existing_pythonpath
    return subprocess.call(command, cwd=ROOT, env=environment)


if __name__ == "__main__":
    raise SystemExit(main())
