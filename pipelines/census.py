#!/usr/bin/env python3
"""Read-only census of a factory run directory.

Recursively scans every *.jsonl, classifies record kinds, and histograms
nested sim_or_real labels. Prints JSON on stdout. Never writes into run_dir.

The `mill_mix` section reports records whose mill signals (declared factory,
mill id prefix, goal family) belong to a different factory than the directory
they were published under. Those findings are also subtracted from the
destination's `eligible` denominator. Detection and mill ownership come only
from `mill_family.py`; `leftover` in an id is never itself evidence.

Usage: python3 pipelines/census.py <run_dir>
"""

import json
import sys
from collections import Counter
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from mill_family import (  # noqa: E402
    MillFinding,
    MillIndex,
    factory_identity_for_path as shared_factory_identity_for_path,
    summarize as summarize_mill_mix,
)
from round_txn import (  # noqa: E402
    FACTORY_QUOTAS,
    TransactionError,
    committed_jsonl_paths,
    marker_mode_path,
)
from validate_run import reject_json_constant  # noqa: E402

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

__all__ = [
    "KINDS",
    "SIM_BUCKETS",
    "THALAMIC_REQUIRED",
    "bucket_sim_or_real",
    "census_dir",
    "classify_kind",
    "factory_for_path",
    "factory_identity_for_path",
    "iter_sim_or_real",
    "main",
    "visible_jsonl_paths",
]


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


def _enclosing_marker_root(run_dir: Path, path: Path) -> Path | None:
    """Return the nearest marker-mode factory enclosing ``path``."""

    current = path.parent
    while True:
        if marker_mode_path(current) is not None:
            return current
        if current == run_dir:
            return None
        parent = current.parent
        if parent == current:  # Defensive: ``relative_to`` should prevent this.
            return None
        current = parent


def visible_jsonl_paths(run_dir: Path) -> list[Path]:
    """Return JSONL visible under the round transaction contract.

    Legacy trees without marker mode remain recursively visible. Once an
    enclosing factory has entered marker mode, only paths returned by
    ``committed_jsonl_paths`` may contribute to census or audit denominators.
    """

    run_dir = Path(run_dir)
    visible_by_marker_root: dict[Path, set[Path]] = {}
    visible = []
    for path in sorted(run_dir.rglob("*.jsonl")):
        if not path.is_file() or path.is_symlink():
            continue
        marker_root = _enclosing_marker_root(run_dir, path)
        if marker_root is None:
            visible.append(path)
            continue
        if marker_root not in visible_by_marker_root:
            visible_by_marker_root[marker_root] = {
                candidate.resolve()
                for candidate in committed_jsonl_paths(marker_root)
            }
        if path.resolve() in visible_by_marker_root[marker_root]:
            visible.append(path)
    return visible


def factory_identity_for_path(
    run_dir: Path, path: Path
) -> tuple[str, bool]:
    """Return factory name plus independent root-verification evidence."""

    return shared_factory_identity_for_path(
        run_dir,
        path,
        marker_root=_enclosing_marker_root(run_dir, path),
        known_factories=FACTORY_QUOTAS,
    )


def factory_for_path(run_dir: Path, path: Path) -> str:
    """Return the verified or enclosing factory name for one payload."""

    return factory_identity_for_path(run_dir, path)[0]


def _finding_row(finding: MillFinding) -> dict:
    row = finding.as_dict()
    ref = finding.ref
    if isinstance(ref, tuple) and len(ref) == 2:
        source, line = ref
        row["source"] = str(source)
        row["line"] = line
    return row


def census_dir(run_dir):
    run_dir = Path(run_dir).resolve()
    by_kind = {kind: 0 for kind in KINDS}
    sim_hist = {bucket: 0 for bucket in SIM_BUCKETS}
    by_factory = Counter()
    mills = MillIndex()
    files = 0
    records = 0
    parse_failures = 0
    decode_failures = 0
    unreadable_files = []

    for path in visible_jsonl_paths(run_dir):
        files += 1
        relative = path.relative_to(run_dir)
        factory, factory_verified = factory_identity_for_path(run_dir, path)
        payload = path.read_bytes()
        for lineno, raw_line in enumerate(payload.splitlines(), 1):
            if not raw_line.strip():
                continue
            try:
                line = raw_line.decode("utf-8")
            except UnicodeDecodeError as exc:
                decode_failures += 1
                unreadable_files.append(
                    {
                        "source": relative.as_posix(),
                        "line": lineno,
                        "error": str(exc),
                    }
                )
                continue
            try:
                obj = json.loads(line, parse_constant=reject_json_constant)
            except (json.JSONDecodeError, ValueError):
                parse_failures += 1
                continue
            records += 1
            by_factory[factory] += 1
            mills.add(
                factory,
                obj,
                (relative.as_posix(), lineno),
                factory_verified=factory_verified,
            )
            by_kind[classify_kind(obj)] += 1
            found = list(iter_sim_or_real(obj))
            if not found:
                sim_hist["<missing>"] += 1
                continue
            for value in found:
                sim_hist[bucket_sim_or_real(value)] += 1

    findings = mills.findings()
    quarantined_by_factory = Counter(finding.factory for finding in findings)
    mill_mix = summarize_mill_mix(findings)
    mill_mix["quarantined_records"] = [
        _finding_row(finding) for finding in findings
    ]

    return {
        "run_dir": str(run_dir),
        "files": files,
        "records": records,
        "parse_failures": parse_failures,
        "decode_failures": decode_failures,
        "unreadable_files": unreadable_files,
        "eligible_records": records - len(findings),
        "by_kind": by_kind,
        "sim_or_real": sim_hist,
        "by_factory": dict(sorted(by_factory.items())),
        "eligible_by_factory": {
            factory: by_factory[factory] - quarantined_by_factory[factory]
            for factory in sorted(by_factory)
        },
        "mill_mix": mill_mix,
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
    try:
        report = census_dir(run_dir)
    except TransactionError as exc:
        print(f"census failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
