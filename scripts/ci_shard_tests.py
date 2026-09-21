"""Run a deterministic round-robin shard of the unittest modules."""

from __future__ import annotations

import argparse
import multiprocessing
import os
import sys
import unittest
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


def _run_shard(
    chosen: list[str], coverage_enabled: bool, environment: dict[str, str]
) -> None:
    """Run one shard in a clean Python process."""
    os.chdir(ROOT)
    os.environ.clear()
    os.environ.update(environment)
    sys.path[:0] = [str(ROOT / "tests"), str(ROOT)]

    coverage = None
    if coverage_enabled:
        from coverage import Coverage

        coverage = Coverage(data_suffix=True)
        coverage.start()
    try:
        suite = unittest.defaultTestLoader.loadTestsFromNames(chosen)
        result = unittest.TextTestRunner(buffer=True).run(suite)
        exit_code = 0 if result.wasSuccessful() else 1
    finally:
        if coverage is not None:
            coverage.stop()
            coverage.save()
    raise SystemExit(exit_code)


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

    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(ROOT / "tests")
    if existing_pythonpath:
        environment["PYTHONPATH"] += os.pathsep + existing_pythonpath
    context = multiprocessing.get_context("spawn")
    process = context.Process(
        target=_run_shard,
        args=(chosen, args.coverage, environment),
    )
    process.start()
    process.join()
    return process.exitcode if process.exitcode is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
