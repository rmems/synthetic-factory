#!/usr/bin/env python3
"""Final-output record bindings for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

A curation manifest's ``record_bindings`` list is the bridge between the rows
that actually sit in a cleaned tree and the lane evidence that produced them.
``_normalize_record_bindings`` validates and canonicalizes that list -- unique
output and source coordinates, normalized paths and ids, one lineage row per
declared lane in contract order -- and ``_output_evidence_gate`` authenticates
every final row against it: the row's hash and id, its source hash, and its
lineage, plus coverage in both directions between rows, bindings and retained
lane evidence.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_bindings")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_paths as _paths
    from . import curate_gate_records as _records
    from .check_records import canonical_record_id
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_bindings"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_paths as _paths
    import curate_gate_records as _records
    from check_records import canonical_record_id

GateError = _contract.GateError
EXCLUSION_ACTIONS = _contract.EXCLUSION_ACTIONS
QUARANTINE_ACTIONS = _contract.QUARANTINE_ACTIONS
REQUIRED_LANES = _contract.REQUIRED_LANES
record_sha256 = _digest.record_sha256
_normalized_sha256 = _digest._normalized_sha256
_logical_source_path = _paths._logical_source_path
_normalized_output_path = _paths._normalized_output_path
iter_records = _records.iter_records


# ---------------------------------------------------------------------------
# normalizing the declared record bindings
# ---------------------------------------------------------------------------


def _binding_coordinates(
    raw: dict[str, Any],
    label: str,
    output_coordinates: set[tuple[str, int]],
    source_coordinates: set[tuple[str, int]],
) -> tuple[str, Any, str, Any]:
    """Normalize one binding's output/source coordinates and claim both.

    The line numbers stay ``Any``: they are proven positive integers by the
    loop below, which no static narrowing follows, and the caller re-publishes
    them verbatim.
    """
    output_path = _normalized_output_path(raw.get("output_path"), f"{label}.output_path")
    source_path = _logical_source_path(raw.get("source_path"), f"{label}.source_path")
    output_line = raw.get("output_line")
    source_line = raw.get("source_line")
    for field, value in (("output_line", output_line), ("source_line", source_line)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise GateError(f"{label}.{field} must be a positive integer")
    output_coordinate = (output_path, output_line)
    source_coordinate = (source_path, source_line)
    if output_coordinate in output_coordinates:
        raise GateError(f"{label} duplicates output coordinate {output_path}:{output_line}")
    if source_coordinate in source_coordinates:
        raise GateError(f"{label} duplicates source coordinate {source_path}:{source_line}")
    output_coordinates.add(output_coordinate)
    source_coordinates.add(source_coordinate)
    return output_path, output_line, source_path, source_line


def _binding_output_id(raw: dict[str, Any], label: str) -> Any:
    output_id = raw.get("output_id")
    if output_id is not None and (
        not isinstance(output_id, str) or not output_id.strip() or output_id != output_id.strip()
    ):
        raise GateError(f"{label}.output_id must be null or a normalized non-empty string")
    return output_id


def _lineage_lane_order(
    item: dict[str, Any], lineage_label: str, seen_lane_orders: set[int]
) -> int:
    order = item.get("lane_order")
    if (
        not isinstance(order, int)
        or isinstance(order, bool)
        or not 1 <= order <= len(REQUIRED_LANES)
        or order in seen_lane_orders
    ):
        raise GateError(f"{lineage_label}.lane_order is invalid or duplicated")
    seen_lane_orders.add(order)
    return order


def _binding_lineage(raw: dict[str, Any], label: str) -> list[dict[str, Any]]:
    """One lineage row per declared lane, each matching its lane contract."""
    lineage = raw.get("lineage")
    if not isinstance(lineage, list) or not lineage:
        raise GateError(f"{label}.lineage must be a non-empty list")
    normalized_lineage: list[dict[str, Any]] = []
    seen_lane_orders: set[int] = set()
    for lineage_index, item in enumerate(lineage, 1):
        lineage_label = f"{label}.lineage[{lineage_index}]"
        if not isinstance(item, dict):
            raise GateError(f"{lineage_label} must be an object")
        order = _lineage_lane_order(item, lineage_label, seen_lane_orders)
        transform = item.get("transform")
        version = item.get("version")
        if transform != REQUIRED_LANES[order - 1][1] or not isinstance(version, str):
            raise GateError(f"{lineage_label} does not match its lane contract")
        normalized_lineage.append(
            {
                "lane_order": order,
                "transform": transform,
                "version": version,
                "output_sha256": _normalized_sha256(
                    item.get("output_sha256"), f"{lineage_label}.output_sha256"
                ),
            }
        )
    return normalized_lineage


def _normalize_binding(
    raw: Any,
    label: str,
    output_coordinates: set[tuple[str, int]],
    source_coordinates: set[tuple[str, int]],
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise GateError(f"{label} must be an object")
    output_path, output_line, source_path, source_line = _binding_coordinates(
        raw, label, output_coordinates, source_coordinates
    )
    output_id = _binding_output_id(raw, label)
    normalized_lineage = _binding_lineage(raw, label)
    return {
        "output_path": output_path,
        "output_line": output_line,
        "output_sha256": _normalized_sha256(raw.get("output_sha256"), f"{label}.output_sha256"),
        "output_id": output_id,
        "source_path": source_path,
        "source_line": source_line,
        "source_hash": _normalized_sha256(raw.get("source_hash"), f"{label}.source_hash"),
        "source_record_sha256": _normalized_sha256(
            raw.get("source_record_sha256"), f"{label}.source_record_sha256"
        ),
        "lineage": sorted(normalized_lineage, key=lambda lane_row: lane_row["lane_order"]),
    }


def _normalize_record_bindings(raw_bindings: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_bindings, list) or not raw_bindings:
        raise GateError("curation manifest needs a non-empty record_bindings list")
    normalized: list[dict[str, Any]] = []
    output_coordinates: set[tuple[str, int]] = set()
    source_coordinates: set[tuple[str, int]] = set()
    for index, raw in enumerate(raw_bindings, 1):
        normalized.append(
            _normalize_binding(
                raw, f"record_bindings[{index}]", output_coordinates, source_coordinates
            )
        )
    return sorted(normalized, key=lambda binding: (binding["output_path"], binding["output_line"]))


# ---------------------------------------------------------------------------
# authenticating every final row against source identity and lane evidence
# ---------------------------------------------------------------------------


def _final_output_records(cleaned: Path, errors: list[dict[str, str]]) -> dict[tuple[str, int], Any]:
    actual_by_output: dict[tuple[str, int], Any] = {}
    for relative, line, record in iter_records(cleaned):
        coordinate = (relative, line)
        if record is None:
            errors.append(
                {"source": f"{relative}:{line}", "error": "final output is not valid JSON"}
            )
            continue
        actual_by_output[coordinate] = record
    return actual_by_output


def _binding_coverage(
    bindings: Sequence[dict[str, Any]],
    actual_by_output: dict[tuple[str, int], Any],
    errors: list[dict[str, str]],
) -> dict[tuple[str, int], dict[str, Any]]:
    """Rows without a binding, and bindings without a row."""
    binding_by_output = {
        (binding["output_path"], binding["output_line"]): binding for binding in bindings
    }
    missing_bindings = sorted(set(actual_by_output) - set(binding_by_output))
    extra_bindings = sorted(set(binding_by_output) - set(actual_by_output))
    for path, line in missing_bindings[:10]:
        errors.append({"source": f"{path}:{line}", "error": "final record has no binding"})
    for path, line in extra_bindings[:10]:
        errors.append({"source": f"{path}:{line}", "error": "binding has no final record"})
    return binding_by_output


def _lane_evidence_by_source(
    prepared_lanes: Sequence[dict[str, Any]],
) -> tuple[dict[tuple[str, int], list[dict[str, Any]]], set[tuple[str, int]]]:
    entries_by_source: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    terminal_sources: set[tuple[str, int]] = set()
    for lane in prepared_lanes:
        for entry in lane["entries"]:
            source_key = entry["_source_key"]
            action = str(entry.get("action") or "").strip().lower()
            if action in EXCLUSION_ACTIONS | QUARANTINE_ACTIONS:
                terminal_sources.add(source_key)
            if entry.get("output_hash") is not None:
                entries_by_source[source_key].append(entry)
    return entries_by_source, terminal_sources


def _source_coverage(
    entries_by_source: dict[tuple[str, int], list[dict[str, Any]]],
    terminal_sources: set[tuple[str, int]],
    bindings: Sequence[dict[str, Any]],
    errors: list[dict[str, str]],
) -> None:
    """Retained lane evidence without a row, and bindings without evidence."""
    expected_source_keys = set(entries_by_source) - terminal_sources
    bound_source_keys = {(binding["source_path"], binding["source_line"]) for binding in bindings}
    for path, line in sorted(expected_source_keys - bound_source_keys)[:10]:
        errors.append(
            {"source": f"{path}:{line}", "error": "retained lane evidence has no final output"}
        )
    for path, line in sorted(bound_source_keys - expected_source_keys)[:10]:
        errors.append(
            {"source": f"{path}:{line}", "error": "final binding has no retained lane evidence"}
        )


def _authenticate_final_record(
    binding: dict[str, Any],
    record: Any,
    where: str,
    evidence_entries: Sequence[dict[str, Any]],
    errors: list[dict[str, str]],
) -> None:
    """Hash, id, source hash and lineage of one row against its binding."""
    if record_sha256(record) != binding["output_sha256"]:
        errors.append({"source": where, "error": "final record hash mismatches binding"})
    if canonical_record_id(record) != binding["output_id"]:
        errors.append({"source": where, "error": "final record id mismatches binding"})
    source_hashes = {entry.get("source_hash") for entry in evidence_entries}
    if source_hashes != {binding["source_hash"]}:
        errors.append({"source": where, "error": "binding source hash mismatches lane evidence"})
    expected_lineage = sorted(
        (
            entry["lane_order"],
            entry["transform"],
            entry["version"],
            entry["output_hash"],
        )
        for entry in evidence_entries
    )
    actual_lineage = sorted(
        (
            item["lane_order"],
            item["transform"],
            item["version"],
            item["output_sha256"],
        )
        for item in binding["lineage"]
    )
    if actual_lineage != expected_lineage:
        errors.append({"source": where, "error": "binding lineage mismatches lane evidence"})


def _output_evidence_gate(
    cleaned: Path,
    raw_bindings: Any,
    prepared_lanes: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any], dict[tuple[str, int], Any], list[dict[str, Any]]]:
    """Authenticate every final row against source identity and lane evidence."""
    bindings = _normalize_record_bindings(raw_bindings)
    errors: list[dict[str, str]] = []
    actual_by_output = _final_output_records(cleaned, errors)
    binding_by_output = _binding_coverage(bindings, actual_by_output, errors)
    entries_by_source, terminal_sources = _lane_evidence_by_source(prepared_lanes)
    _source_coverage(entries_by_source, terminal_sources, bindings, errors)

    records_by_source: dict[tuple[str, int], Any] = {}
    for coordinate in sorted(set(binding_by_output) & set(actual_by_output)):
        binding = binding_by_output[coordinate]
        record = actual_by_output[coordinate]
        source_key = (binding["source_path"], binding["source_line"])
        records_by_source[source_key] = record
        _authenticate_final_record(
            binding,
            record,
            f"{coordinate[0]}:{coordinate[1]}",
            entries_by_source.get(source_key, []),
            errors,
        )

    report = {
        "tool": "curate_gate final-output binding verifier",
        "passed": not errors,
        "records": len(actual_by_output),
        "bindings": len(bindings),
        "invalid_bindings": len(errors),
        "examples": errors[:5],
    }
    return report, records_by_source, bindings


if __package__:
    _expose_package_sibling(__name__)
