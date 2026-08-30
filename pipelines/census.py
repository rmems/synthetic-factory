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

from curate_identity import default_registry  # noqa: E402
from mill_family import (  # noqa: E402
    MillFinding,
    MillIndex,
    factory_identity_for_path as shared_factory_identity_for_path,
    summarize as summarize_mill_mix,
)
from record_kind import (  # noqa: E402
    DECLARED_KINDS,
    THALAMIC_REQUIRED,
    classify_kind,
)
from round_txn import (  # noqa: E402
    TransactionError,
    committed_jsonl_paths,
    marker_mode_path,
)
from validate_run import reject_json_constant  # noqa: E402

KINDS = (
    "thalamic",
    "preference",
    "bridge_pair",
    "multi_agent",
    "safety_case",
    "episode",
    "hardware_parity",
    "nir_equivalence",
    "unknown",
)
SIM_BUCKETS = ("real", "real*", "sim*", "hil*", "other", "<missing>")

__all__ = [
    "DECLARED_KINDS",
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
    "reject_json_constant",
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


def _finding_row(finding: MillFinding) -> dict:
    row = finding.as_dict()
    ref = finding.ref
    if isinstance(ref, tuple) and len(ref) == 2:
        source, line = ref
        row["source"] = str(source)
        row["line"] = line
    return row


def _read_census_records(path: Path, source: str):
    """Return decoded records plus bounded parse/decode diagnostics."""

    decoded = []
    parse_failures = 0
    unreadable = []
    for lineno, raw_line in enumerate(path.read_bytes().splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            line = raw_line.decode("utf-8")
        except UnicodeDecodeError as exc:
            unreadable.append(
                {"source": source, "line": lineno, "error": str(exc)}
            )
            continue
        try:
            decoded.append(
                (lineno, json.loads(line, parse_constant=reject_json_constant))
            )
        except (json.JSONDecodeError, ValueError):
            parse_failures += 1
    return decoded, parse_failures, unreadable


def _record_simulation_buckets(obj) -> Counter:
    values = list(iter_sim_or_real(obj))
    if not values:
        return Counter({"<missing>": 1})
    return Counter(bucket_sim_or_real(value) for value in values)


class _CensusTotals:
    """Every axis one census pass accumulates while it walks a run.

    These nine counters are one accumulator in practice: a single decoded
    record advances several of them together, and none is meaningful without
    the rest. Holding them as one value keeps reading a file, tallying a
    record and assembling the report as three short steps instead of one
    method that owns all three plus nine locals. It is a plain mutable class
    rather than one of this module's frozen value objects because advancing
    in place during the scan is the whole point.
    """

    def __init__(self):
        self.by_kind = {kind: 0 for kind in KINDS}
        self.sim_hist = {bucket: 0 for bucket in SIM_BUCKETS}
        self.by_factory = Counter()
        self.mills = MillIndex()
        self.files = 0
        self.records = 0
        self.parse_failures = 0
        self.decode_failures = 0
        self.unreadable_files = []

    def add_file(self, run_dir: Path, path: Path) -> None:
        """Read one payload file into the running totals."""

        self.files += 1
        source = path.relative_to(run_dir).as_posix()
        factory, factory_verified = factory_identity_for_path(run_dir, path)
        decoded, parse_failures, unreadable = _read_census_records(
            path, source
        )
        self.parse_failures += parse_failures
        self.decode_failures += len(unreadable)
        self.unreadable_files.extend(unreadable)
        for lineno, obj in decoded:
            self._add_record(obj, factory, factory_verified, (source, lineno))

    def _add_record(self, obj, factory, factory_verified, ref) -> None:
        """Tally one decoded record against every census axis."""

        self.records += 1
        self.by_factory[factory] += 1
        self.mills.add(factory, obj, ref, factory_verified=factory_verified)
        self.by_kind[classify_kind(obj)] += 1
        for bucket, count in _record_simulation_buckets(obj).items():
            self.sim_hist[bucket] += count

    def report(self, run_dir: Path) -> dict:
        """Return the census mapping these totals describe."""

        findings = self.mills.findings()
        quarantined_by_factory = Counter(
            finding.factory for finding in findings
        )
        mill_mix = summarize_mill_mix(findings)
        mill_mix["quarantined_records"] = [
            _finding_row(finding) for finding in findings
        ]
        return {
            "run_dir": str(run_dir),
            "files": self.files,
            "records": self.records,
            "parse_failures": self.parse_failures,
            "decode_failures": self.decode_failures,
            "unreadable_files": self.unreadable_files,
            "eligible_records": self.records - len(findings),
            "by_kind": self.by_kind,
            "sim_or_real": self.sim_hist,
            "by_factory": dict(sorted(self.by_factory.items())),
            "eligible_by_factory": {
                factory: self.by_factory[factory]
                - quarantined_by_factory[factory]
                for factory in sorted(self.by_factory)
            },
            "mill_mix": mill_mix,
        }


def census_dir(run_dir):
    run_dir = Path(run_dir).resolve()
    totals = _CensusTotals()
    for path in visible_jsonl_paths(run_dir):
        totals.add_file(run_dir, path)
    return totals.report(run_dir)
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
