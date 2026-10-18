"""Run one deterministic, duration-weighted shard of the unittest modules.

Modules are assigned by longest-processing-time-first (LPT) greedy bin packing
over the committed weights table ``ci_shard_weights.json`` next to this script:
modules are taken heaviest first, ties broken by module name, and each one goes
to the shard with the smallest running total, ties broken by the lower shard
index. A module missing from the table weighs the table's ``default_weight``,
so a new test file is still assigned deterministically. Every plan is checked
to place each discovered module in exactly one shard, and the run fails closed
otherwise. Within a shard the modules run in name order.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import unittest
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS_PATH = Path(__file__).resolve().with_name("ci_shard_weights.json")
WEIGHTS_SCHEMA = "ci-shard-weights-v1"
# No test module is weighed at more than a day; CI cancels a shard after 25 minutes.
MAX_WEIGHT_SECONDS = 86_400


class ShardPlanError(ValueError):
    """The weights table or a shard plan is invalid, so the run fails closed."""


@dataclass(frozen=True)
class ShardWeights:
    """Per-module durations in seconds, with ``default`` for modules not in ``table``."""

    table: Mapping[str, float]
    default: float

    def of(self, module: str) -> float:
        """Return the recorded weight of ``module``, or the default weight."""
        return self.table.get(module, self.default)


def discover_modules(root: Path = ROOT) -> list[str]:
    """Return sorted test module stems discovered directly under ``tests``."""
    return sorted(path.stem for path in (root / "tests").glob("test_*.py"))


def _positive_seconds(value: object, where: str) -> float:
    """Return ``value`` as a float, refusing non-numbers and values outside (0, MAX_WEIGHT_SECONDS].

    The range test runs before any float conversion: comparing an ``int`` with a ``float`` is
    exact in Python, so a huge JSON integer, NaN and infinity are all refused without overflow.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ShardPlanError(f"{where} must be a number of seconds, got {type(value).__name__}")
    if not 0 < value <= MAX_WEIGHT_SECONDS:
        raise ShardPlanError(f"{where} must be above 0 and at most {MAX_WEIGHT_SECONDS} seconds")
    return float(value)


def parse_weights(document: object) -> ShardWeights:
    """Validate a decoded weights table and return its per-module weights."""
    if not isinstance(document, dict) or document.get("schema") != WEIGHTS_SCHEMA:
        raise ShardPlanError(f"weights table must be a {WEIGHTS_SCHEMA} object")
    table = document.get("weights")
    if not isinstance(table, dict):
        raise ShardPlanError("weights table must map test module names to seconds")
    default = _positive_seconds(document.get("default_weight"), "default_weight")
    parsed = {
        module: _positive_seconds(seconds, f"weights[{module!r}]")
        for module, seconds in table.items()
    }
    return ShardWeights(parsed, default)


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Decode one JSON object, refusing a repeated key instead of keeping the last value."""
    decoded = dict(pairs)
    if len(decoded) != len(pairs):
        repeated = sorted(
            key for key, count in Counter(key for key, _ in pairs).items() if count > 1
        )
        raise ShardPlanError(f"weights table repeats keys: {repeated}")
    return decoded


def load_weights(path: Path | None = None) -> ShardWeights:
    """Load and validate the committed weights table (or the one at ``path``)."""
    with (path or WEIGHTS_PATH).open(encoding="utf-8") as handle:
        return parse_weights(json.load(handle, object_pairs_hook=_unique_keys))


def assign_shards(modules: Iterable[str], shards: int, weights: ShardWeights) -> list[list[str]]:
    """Pack ``modules`` into ``shards`` bins: heaviest first, each into the lightest bin."""
    if shards < 1:
        raise ShardPlanError(f"shards must be at least 1, got {shards}")
    loads = [0.0] * shards
    plan: list[list[str]] = [[] for _ in range(shards)]
    for module in sorted(set(modules), key=lambda name: (-weights.of(name), name)):
        target = min(range(shards), key=lambda index: (loads[index], index))
        plan[target].append(module)
        loads[target] += weights.of(module)
    return [sorted(shard) for shard in plan]


def check_partition(modules: Iterable[str], plan: Sequence[Sequence[str]]) -> None:
    """Fail closed unless ``plan`` places every one of ``modules`` in exactly one shard."""
    expected = set(modules)
    assigned = Counter(module for shard in plan for module in shard)
    missing = sorted(expected.difference(assigned))
    extra = sorted(set(assigned).difference(expected))
    repeated = sorted(module for module, count in assigned.items() if count > 1)
    problems = {"missing": missing, "extra": extra, "repeated": repeated}
    if any(problems.values()):
        details = " ".join(f"{kind}={names}" for kind, names in problems.items())
        raise ShardPlanError(f"shard plan is not a partition: {details}")


def plan_shards(modules: Sequence[str], shards: int, weights: ShardWeights) -> list[list[str]]:
    """Return the checked LPT plan of ``modules`` over ``shards`` shards."""
    plan = assign_shards(modules, shards, weights)
    check_partition(modules, plan)
    return plan


def shard_modules(
    modules: list[str],
    shard: int,
    shards: int,
    weights: ShardWeights | None = None,
) -> list[str]:
    """Select one deterministic duration-weighted shard from ``modules``."""
    if not 0 <= shard < shards:
        raise ShardPlanError(f"shard must satisfy 0 <= shard < {shards}, got {shard}")
    if weights is None:
        weights = load_weights()
    return plan_shards(modules, shards, weights)[shard]


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

    try:
        chosen = shard_modules(discover_modules(), args.shard, args.shards)
    except (OSError, ValueError) as error:
        parser.error(f"cannot plan the test shards: {error}")
    if args.list:
        print("\n".join(chosen))
        return 0

    return run_selected_modules(chosen, coverage=args.coverage)


if __name__ == "__main__":
    raise SystemExit(main())
