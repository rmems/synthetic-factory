#!/usr/bin/env python3
"""Record-level lane composition for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; ``compose`` is re-exported from ``curate_gate`` behind a thin
wrapper that supplies the facade's ``RAW_OUTPUT_ROOT`` so tests that patch that
global keep steering the destination refusal.

Composition walks the prepared lanes in plan order. A terminal exclusion or
quarantine suppresses its source record for every lane, earlier or later. A
second retained output for one source identity is three-way merged onto the
composed record, and every supersession is written into the manifest so the
lineage of each emitted line is reviewable.
"""

from __future__ import annotations

import copy
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, NamedTuple, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_compose")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_lanes as _lanes
    from . import curate_gate_merge as _merge
    from . import curate_gate_paths as _paths
    from .check_records import canonical_record_id
    from .exact_json import dumps_exact_json
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_compose"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_lanes as _lanes
    import curate_gate_merge as _merge
    import curate_gate_paths as _paths
    from check_records import canonical_record_id
    from exact_json import dumps_exact_json

GateError = _contract.GateError
EXCLUSION_ACTIONS = _contract.EXCLUSION_ACTIONS
QUARANTINE_ACTIONS = _contract.QUARANTINE_ACTIONS
file_sha256 = _digest.file_sha256
record_sha256 = _digest.record_sha256
_assert_disjoint_trees = _paths._assert_disjoint_trees
_assert_new_destination = _paths._assert_new_destination
_merge_lane_delta = _merge._merge_lane_delta
MergeScope = _merge.MergeScope
prepare_lanes = _lanes.prepare_lanes

_SourceKey = tuple[str, int]


def _assert_lanes_outside_destination(
    prepared_lanes: Sequence[dict[str, Any]], logical_destination: Path
) -> None:
    for lane in prepared_lanes:
        outputs_dir = lane["outputs_dir"]
        if outputs_dir == logical_destination or logical_destination in outputs_dir.parents:
            raise GateError(
                f"lane {lane['order']} ({lane['transform']}) outputs live inside the "
                f"cleaned destination: {outputs_dir}"
            )
        if outputs_dir in logical_destination.parents:
            raise GateError(
                f"cleaned destination is nested inside lane {lane['order']} "
                f"({lane['transform']}) outputs: {outputs_dir}"
            )


def _create_destination(destination: Path) -> None:
    try:
        destination.mkdir(parents=True)
    except FileExistsError as exc:
        raise GateError(
            f"refusing to overwrite an existing cleaned destination: {destination}"
        ) from exc


def _lineage_entry(lane: dict[str, Any], emitted: dict[str, Any]) -> dict[str, Any]:
    return {
        "lane_order": lane["order"],
        "transform": lane["transform"],
        "version": lane["version"],
        "output_sha256": emitted["output_hash"],
    }


class _ComposeState(NamedTuple):
    """The three accumulators a composition folds every emitted record into."""

    records: dict[_SourceKey, dict[str, Any]]
    terminal_actions: dict[_SourceKey, dict[str, Any]]
    supersessions: list[dict[str, Any]]


def _apply_terminal_entries(lane: dict[str, Any], composed: _ComposeState) -> None:
    """Record the lane's exclusions and quarantines; drop any earlier composed record."""
    state = composed.records
    terminal_actions = composed.terminal_actions
    supersessions = composed.supersessions
    for entry in lane["entries"]:
        action = str(entry.get("action") or "").strip().lower()
        if action not in EXCLUSION_ACTIONS | QUARANTINE_ACTIONS:
            continue
        terminal_actions[entry["_source_key"]] = entry
        previous = state.pop(entry["_source_key"], None)
        if previous is not None:
            supersessions.append(
                {
                    "source_path": entry["source_path"],
                    "source_line": entry["source_line"],
                    "superseded_path": previous["relative_path"],
                    "superseded_transform": previous["transform"],
                    "superseded_order": previous["lane_order"],
                    "superseded_sha256": previous["output_hash"],
                    "winning_transform": lane["transform"],
                    "winning_order": lane["order"],
                    "winning_action": action,
                    "winning_sha256": None,
                }
            )


def _suppression(
    lane: dict[str, Any], emitted: dict[str, Any], terminal: dict[str, Any]
) -> dict[str, Any]:
    return {
        "source_path": emitted["source_path"],
        "source_line": emitted["source_line"],
        "suppressed_path": emitted["relative_path"],
        "suppressed_transform": lane["transform"],
        "suppressed_order": lane["order"],
        "suppressed_sha256": emitted["output_hash"],
        "winning_transform": terminal["transform"],
        "winning_order": terminal["lane_order"],
        "winning_action": terminal["action"],
        "winning_sha256": None,
    }


def _composed_record(
    lane: dict[str, Any],
    emitted: dict[str, Any],
    previous: dict[str, Any],
    supersessions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Merge this lane's delta onto the composed record and log the supersession."""
    merged_record = _merge_lane_delta(
        emitted["source_record"],
        previous["record"],
        emitted["record"],
        MergeScope(emitted["source_key"], lane["transform"]),
    )
    merged_hash = record_sha256(merged_record)
    supersessions.append(
        {
            "source_path": emitted["source_path"],
            "source_line": emitted["source_line"],
            "superseded_path": previous["relative_path"],
            "superseded_transform": previous["transform"],
            "superseded_order": previous["lane_order"],
            "superseded_sha256": previous["output_hash"],
            "winning_path": emitted["relative_path"],
            "winning_transform": lane["transform"],
            "winning_order": lane["order"],
            "winning_action": "record_composition",
            "winning_lane_output_sha256": emitted["output_hash"],
            "winning_sha256": merged_hash,
        }
    )
    return {
        **emitted,
        "record": merged_record,
        "output_hash": merged_hash,
        "lane_output_hash": emitted["output_hash"],
        "lineage": [*previous["lineage"], _lineage_entry(lane, emitted)],
    }


def _apply_emitted_record(
    lane: dict[str, Any],
    emitted: dict[str, Any],
    composed: _ComposeState,
) -> None:
    """Suppress, merge, or admit one emitted record by its source identity."""
    state = composed.records
    supersessions = composed.supersessions
    terminal = composed.terminal_actions.get(emitted["source_key"])
    if terminal is not None:
        supersessions.append(_suppression(lane, emitted, terminal))
        return
    previous = state.get(emitted["source_key"])
    if previous is not None:
        state[emitted["source_key"]] = _composed_record(lane, emitted, previous, supersessions)
        return
    state[emitted["source_key"]] = {
        **emitted,
        "lane_output_hash": emitted["output_hash"],
        "lineage": [_lineage_entry(lane, emitted)],
    }


def _lane_summary(lane: dict[str, Any]) -> dict[str, Any]:
    return {
        "order": lane["order"],
        "bead": lane["bead"],
        "transform": lane["transform"],
        "version": lane["version"],
        "outputs": str(lane["outputs_dir"]),
        "manifest": str(lane["manifest_path"]),
        "files": len(lane["input_files"]),
        "records": len(lane["records"]),
    }


def _record_binding(relative: str, output_line: int, item: dict[str, Any]) -> dict[str, Any]:
    return {
        "output_path": relative,
        "output_line": output_line,
        "output_sha256": item["output_hash"],
        "output_id": canonical_record_id(item["record"]),
        "source_path": item["source_path"],
        "source_line": item["source_line"],
        "source_hash": item["source_hash"],
        "source_record_sha256": item["source_record_sha256"],
        "lineage": copy.deepcopy(item["lineage"]),
    }


def _output_summary(relative: str, target: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    """The written file's digest and the distinct lane contributions behind it."""
    lineage = sorted(
        {
            (
                contributor["lane_order"],
                contributor["transform"],
                contributor["version"],
                contributor["output_sha256"],
            )
            for item in records
            for contributor in item["lineage"]
        }
    )
    return {
        "path": relative,
        "sha256": file_sha256(target),
        "bytes": target.stat().st_size,
        "records": len(records),
        "lineage": [
            {
                "lane_order": order,
                "transform": transform,
                "version": version,
                "output_sha256": output_sha256,
            }
            for order, transform, version, output_sha256 in lineage
        ],
    }


def _composed_line(item):
    record = item["record"]
    if record.get("family") == "neuromorphic-fault-recovery":
        payload = item.get("source_bytes")
        if not isinstance(payload, bytes) or record_sha256(record) != item["source_record_sha256"]:
            raise GateError("native simulator composition must preserve authenticated source bytes")
        return payload
    return (dumps_exact_json(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _composed_payload(records):
    lines = [_composed_line(item) for item in records]
    if any(not line.endswith(b"\n") for line in lines[:-1]):
        raise GateError("unterminated native source cannot precede another composed record")
    return b"".join(lines)


def _write_composed_path(
    destination: Path, relative: str, records: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Write one output file in source order; return its summary and line bindings."""
    records.sort(key=lambda item: (item["source_path"], item["source_line"]))
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_composed_payload(records))
    bindings = [
        _record_binding(relative, output_line, item) for output_line, item in enumerate(records, 1)
    ]
    return _output_summary(relative, target, records), bindings


def _write_composed_tree(
    destination: Path, state: dict[_SourceKey, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Group the composed records by output path and write each file in path order."""
    by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for emitted in state.values():
        by_path[emitted["relative_path"]].append(emitted)

    outputs: list[dict[str, Any]] = []
    record_bindings: list[dict[str, Any]] = []
    for relative, records in sorted(by_path.items()):
        output, bindings = _write_composed_path(destination, relative, records)
        outputs.append(output)
        record_bindings.extend(bindings)
    return outputs, record_bindings


class ComposeTarget(NamedTuple):
    """Where a composition writes, what it is reported as, and the raw root it may not touch."""

    destination: Path
    raw_output_root: Path
    logical_destination: Path | None = None


def compose(
    plan: dict[str, Any],
    target: ComposeTarget,
    prepared_lanes: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Three-way-compose authenticated lane deltas by source identity."""
    raw_output_root = target.raw_output_root
    destination = Path(target.destination).resolve()
    logical_destination = Path(target.logical_destination or destination).resolve()
    _assert_disjoint_trees(
        plan["source_run_dir"],
        logical_destination,
        source_label="source_run",
        destination_label="cleaned destination",
    )
    _assert_new_destination(destination, "cleaned destination", raw_output_root)
    prepared_lanes = list(prepared_lanes or prepare_lanes(plan))
    _assert_lanes_outside_destination(prepared_lanes, logical_destination)
    _create_destination(destination)

    composed = _ComposeState({}, {}, [])
    state = composed.records
    lane_summaries: list[dict[str, Any]] = []
    inputs: list[dict[str, Any]] = []
    for lane in prepared_lanes:
        _apply_terminal_entries(lane, composed)
        for emitted in lane["records"]:
            _apply_emitted_record(lane, emitted, composed)
        inputs.extend(lane["input_files"])
        lane_summaries.append(_lane_summary(lane))

    if not state:
        raise GateError("record-level lane composition produced an empty corpus")
    outputs, record_bindings = _write_composed_tree(destination, state)
    return {
        "destination": logical_destination,
        "composition_order": lane_summaries,
        "inputs": inputs,
        "outputs": outputs,
        "record_bindings": record_bindings,
        "supersessions": composed.supersessions,
    }


if __package__:
    _expose_package_sibling(__name__)
