"""Run a deterministic round-robin shard of the unittest modules."""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
import unittest
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]


def discover_modules(root: Path = ROOT) -> list[str]:
    """Return sorted test module stems discovered directly under ``tests``."""
    return sorted(path.stem for path in (root / "tests").glob("test_*.py"))


def shard_modules(modules: list[str], shard: int, shards: int) -> list[str]:
    """Select one deterministic round-robin shard from ``modules``."""
    return [module for index, module in enumerate(modules) if index % shards == shard]


@contextlib.contextmanager
def _tests_import_path(root: Path = ROOT) -> Iterator[None]:
    """Prepend repo root and ``tests/`` like ``python -m unittest`` from ``root``."""
    root_entry = str(root)
    tests_entry = str(root / "tests")
    prior_path = sys.path.copy()
    prior_pythonpath = os.environ.get("PYTHONPATH")
    sys.path.insert(0, tests_entry)
    sys.path.insert(0, root_entry)
    path_entries = [root_entry, tests_entry]
    if prior_pythonpath:
        path_entries.append(prior_pythonpath)
    os.environ["PYTHONPATH"] = os.pathsep.join(path_entries)
    try:
        yield
    finally:
        sys.path[:] = prior_path
        if prior_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = prior_pythonpath


def run_selected_modules(
    modules: list[str],
    *,
    coverage: bool,
    root: Path = ROOT,
) -> int:
    """Run ``modules`` like ``python -m unittest -b`` with root and ``tests/`` on the path."""
    prior_cwd = Path.cwd()
    os.chdir(root)
    try:
        with _tests_import_path(root):
            cov = None
            if coverage:
                import coverage as coverage_mod

                cov = coverage_mod.Coverage(data_suffix=True)
                cov.start()
            try:
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromNames(modules)
                runner = unittest.TextTestRunner(buffer=True)
                result = runner.run(suite)
                return 0 if result.wasSuccessful() else 1
            finally:
                if cov is not None:
                    cov.stop()
                    cov.save()
    finally:
        os.chdir(prior_cwd)


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

    return run_selected_modules(chosen, coverage=args.coverage)


if __name__ == "__main__":
    raise SystemExit(main())
