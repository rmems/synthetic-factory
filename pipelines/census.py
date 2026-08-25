#!/usr/bin/env python3
"""Read-only census of a factory run directory.

Recursively scans every *.jsonl, classifies record kinds, and histograms
nested sim_or_real labels. Prints JSON on stdout. Never writes into run_dir.

The ``mill_mix`` section reports records whose mill signals (declared factory,
mill id prefix, goal family) belong to a different factory than the directory
they were published under. See ``mill_family.py``.

Usage: python3 pipelines/census.py <run_dir>
"""

import json
import sys
from collections import Counter
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from mill_family import MillIndex, summarize as summarize_mill_mix  # noqa: E402
from round_txn import FACTORY_QUOTAS  # noqa: E402

THALAMIC_REQUIRED = (
    "state",
    "proposed_action",
    "safety_decision",
    "executed_action",
    "future_outcome",
    "reward_components",
)

KINDS = (
    "thalamic",
    "preference",
    "bridge_pair",
    "multi_agent",
    "safety_case",
    "episode",
    "unknown",
)
SIM_BUCKETS = ("real", "real*", "sim*", "hil*", "other", "<missing>")


def classify_kind(obj):
    if not isinstance(obj, dict):
        return "unknown"
    if all(k in obj for k in THALAMIC_REQUIRED):
        return "thalamic"
    if "chosen" in obj and "rejected" in obj:
        return "preference"
    if "language_view" in obj and "spike_events" in obj:
        return "bridge_pair"
    if "case_type" in obj:
        return "safety_case"
    if "transcript" in obj and "agents" in obj:
        return "multi_agent"
    if "goal" in obj and "steps" in obj:
        return "episode"
    return "unknown"


def bucket_sim_or_real(value):
    if not isinstance(value, str):
        return "other"
    low = value.strip().lower()
    if low == "real":
        return "real"
    if (
        low.startswith("real")
        or low.startswith("live")
        or "production" in low
        or "actions live" in low
    ):
        return "real*"
    if "simulat" in low:
        return "sim*"
    if "hardware-in-the-loop" in low or low.startswith("hil"):
        return "hil*"
    return "other"


def iter_sim_or_real(obj):
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key == "sim_or_real":
                yield val
            yield from iter_sim_or_real(val)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_sim_or_real(item)


def census_dir(run_dir):
    run_dir = Path(run_dir).resolve()
    by_kind = {kind: 0 for kind in KINDS}
    sim_hist = {bucket: 0 for bucket in SIM_BUCKETS}
    by_factory = Counter()
    mills = MillIndex()
    files = 0
    records = 0
    parse_failures = 0

    for path in sorted(run_dir.rglob("*.jsonl")):
        files += 1
        relative = path.relative_to(run_dir)
        # The run's first directory component is the factory root. Recursive
        # work/archive directories are storage detail, not factory identity.
        if run_dir.name in FACTORY_QUOTAS or run_dir.name.endswith("-factory"):
            factory = run_dir.name
        else:
            factory = (
                relative.parts[0]
                if len(relative.parts) > 1
                else run_dir.name
            )
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                parse_failures += 1
                continue
            records += 1
            by_factory[factory] += 1
            mills.add(factory, obj, (relative.as_posix(), lineno))
            by_kind[classify_kind(obj)] += 1
            found = list(iter_sim_or_real(obj))
            if not found:
                sim_hist["<missing>"] += 1
                continue
            for value in found:
                sim_hist[bucket_sim_or_real(value)] += 1

    return {
        "run_dir": str(run_dir),
        "files": files,
        "records": records,
        "parse_failures": parse_failures,
        "by_kind": by_kind,
        "sim_or_real": sim_hist,
        "by_factory": dict(sorted(by_factory.items())),
        "mill_mix": summarize_mill_mix(mills.findings()),
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("Usage: python3 pipelines/census.py <run_dir>", file=sys.stderr)
        return 2
    run_dir = Path(argv[0])
    if not run_dir.is_dir():
        print(f"census: not a directory: {run_dir}", file=sys.stderr)
        return 2
    print(json.dumps(census_dir(run_dir), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
