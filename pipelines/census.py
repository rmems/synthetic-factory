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

from curate_identity import default_registry  # noqa: E402
from mill_family import (  # noqa: E402
    MillIndex,
    factory_identity_for_path as shared_factory_identity_for_path,
    summarize as summarize_mill_mix,
)
from record_kind import THALAMIC_REQUIRED, classify_kind  # noqa: E402
from round_txn import (  # noqa: E402
    TransactionError,
    committed_jsonl_paths,
    marker_mode_path,
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


# Near-real labels: not the bare word ``real``, but still claiming a live or
# production run rather than a simulation.
_REAL_STAR_PREFIXES = ("real", "live")
_REAL_STAR_SUBSTRINGS = ("production", "actions live")


def _is_real_star(low):
    """True for a label that claims a live/production run without being ``real``."""
    if low.startswith(_REAL_STAR_PREFIXES):
        return True
    return any(fragment in low for fragment in _REAL_STAR_SUBSTRINGS)


def _is_hil(low):
    """True for a hardware-in-the-loop label."""
    return "hardware-in-the-loop" in low or low.startswith("hil")


def bucket_sim_or_real(value):
    if not isinstance(value, str):
        return "other"
    low = value.strip().lower()
    if low == "real":
        return "real"
    if _is_real_star(low):
        return "real*"
    if "simulat" in low:
        return "sim*"
    if _is_hil(low):
        return "hil*"
    return "other"


def _iter_mapping_sim_or_real(obj):
    """Yield ``sim_or_real`` values carried by one mapping and its children."""
    for key, val in obj.items():
        if key == "sim_or_real":
            yield val
        yield from iter_sim_or_real(val)


def iter_sim_or_real(obj):
    if isinstance(obj, dict):
        yield from _iter_mapping_sim_or_real(obj)
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
        if parent == current:  # Defensive: ``relative_to`` should prevent it.
            return None
        current = parent


def visible_jsonl_paths(run_dir: Path) -> list[Path]:
    """Return JSONL visible under the round transaction contract."""

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
        # The reviewed factory registry is the source of truth for which
        # directory names are a known factory. The round-quota table
        # (FACTORY_QUOTAS) only covers factories with an active quota; a
        # registered-but-unquota'd factory (e.g. an identity-only generator)
        # would otherwise read as unverified, and an unverified root lets an
        # all-foreign batch redefine the destination from its own payload
        # declaration -- so this report-only audit would miss the very
        # contamination it exists to surface. Matches curate_agentic.
        known_factories=default_registry().by_path_id,
    )


def factory_for_path(run_dir: Path, path: Path) -> str:
    """Return the verified or enclosing factory name for one payload."""

    return factory_identity_for_path(run_dir, path)[0]


# Sentinel for a line that did not decode. A dedicated object, because a
# record may legitimately be ``None``.
_UNDECODABLE = object()


def _decode_lines(path):
    """Yield (line number, decoded record) for every non-blank line.

    A line that is not decodable yields ``_UNDECODABLE`` so the caller counts
    it as a parse failure rather than a record.
    """

    for lineno, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            yield lineno, json.loads(line)
        except json.JSONDecodeError:
            yield lineno, _UNDECODABLE


def _count_sim_or_real(obj, sim_hist):
    """Histogram one record's nested ``sim_or_real`` labels."""

    found = list(iter_sim_or_real(obj))
    if not found:
        sim_hist["<missing>"] += 1
        return
    for value in found:
        sim_hist[bucket_sim_or_real(value)] += 1


def census_dir(run_dir):
    run_dir = Path(run_dir).resolve()
    by_kind = {kind: 0 for kind in KINDS}
    sim_hist = {bucket: 0 for bucket in SIM_BUCKETS}
    by_factory = Counter()
    mills = MillIndex()
    files = 0
    records = 0
    parse_failures = 0

    for path in visible_jsonl_paths(run_dir):
        files += 1
        relative = path.relative_to(run_dir)
        factory, factory_verified = factory_identity_for_path(run_dir, path)
        for lineno, obj in _decode_lines(path):
            if obj is _UNDECODABLE:
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
            _count_sim_or_real(obj, sim_hist)

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
    try:
        report = census_dir(run_dir)
    except TransactionError as exc:
        print(f"census failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
