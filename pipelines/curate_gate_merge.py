#!/usr/bin/env python3
"""Three-way merge primitives for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

The immutable source record is the merge base. Each lane output is a delta
from that base: changes at disjoint JSON paths compose, a lane that repeats an
earlier lane's change is a no-op, and two different changes to the same path
fail closed with the JSON pointer of the conflict. ``_MISSING`` is the single
sentinel for "this key is absent" and must stay one object, because the merge
compares it by identity.
"""

from __future__ import annotations

import copy
import io
import json
import sys
from pathlib import Path
from typing import Any, NamedTuple, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_merge")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_paths as _paths
    from .check_records import reject_json_constant
    from .exact_json import parse_finite_json_float
    from .exact_json_compare import same_exact_json
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_merge"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_paths as _paths
    from check_records import reject_json_constant
    from exact_json import parse_finite_json_float
    from exact_json_compare import same_exact_json

GateError = _contract.GateError
sha256_hex = _digest.sha256_hex
_all_jsonl_paths = _digest._all_jsonl_paths
_read_regular_file_snapshot = _digest._read_regular_file_snapshot
_assert_no_symlink = _paths._assert_no_symlink


def _source_line_payload(physical_line):
    if physical_line.endswith(b"\n"):
        return physical_line[:-1].removesuffix(b"\r")
    return physical_line


def _load_source_records(source_run: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """Load the immutable source bytes used as the three-way merge base."""
    records: dict[tuple[str, int], dict[str, Any]] = {}
    paths = _all_jsonl_paths(source_run)
    if not paths:
        raise GateError(f"source_run holds no *.jsonl: {source_run}")
    for path in paths:
        _assert_no_symlink(source_run, path, "source_run")
        relative = path.relative_to(source_run).as_posix()
        payload, _payload_sha256, _payload_bytes = _read_regular_file_snapshot(
            path,
            "source JSONL",
        )
        for line_number, physical_line in enumerate(io.BytesIO(payload), 1):
            raw_line = _source_line_payload(physical_line)
            if not raw_line.strip():
                continue
            record: Any = None
            parse_error: str | None = None
            try:
                text = raw_line.decode("utf-8")
                record = json.loads(
                    text,
                    parse_constant=reject_json_constant,
                    parse_float=parse_finite_json_float,
                )
            # ``UnicodeError`` and ``JSONDecodeError`` are both ``ValueError``
            # subclasses, so one clause covers the decode and the parse.
            except ValueError as exc:
                parse_error = str(exc)
            records[(relative, line_number)] = {
                "record": record,
                "source_hash": sha256_hex(raw_line),
                "source_bytes": physical_line,
                "parse_error": parse_error,
            }
    return records


_MISSING = object()


def _same_json(left: Any, right: Any) -> bool:
    if left is _MISSING or right is _MISSING:
        return left is right
    return same_exact_json(left, right)


def _json_pointer(parts: Sequence[str | int]) -> str:
    if not parts:
        return "/"
    tokens = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(tokens)


class MergeScope(NamedTuple):
    """Which source record, which lane, and where inside the record we are."""

    source_key: tuple[str, int]
    transform: str
    path: tuple[str | int, ...] = ()

    def at(self, part: str | int) -> "MergeScope":
        return self._replace(path=(*self.path, part))


def _merge_lane_delta(
    baseline: Any,
    current: Any,
    lane_value: Any,
    scope: MergeScope,
) -> Any:
    """Apply one independently produced lane delta to the composed record.

    A lane may omit earlier lanes' changes because its output was derived from
    the immutable source record. Changes at disjoint JSON paths compose. The
    gate fails closed when two lanes make incompatible changes at one path.
    """
    if _same_json(lane_value, baseline):
        return copy.deepcopy(current)
    if _same_json(current, baseline):
        return _MISSING if lane_value is _MISSING else copy.deepcopy(lane_value)
    if _same_json(current, lane_value):
        return copy.deepcopy(current)

    if all(isinstance(value, dict) for value in (baseline, current, lane_value)):
        return _merge_object_delta(baseline, current, lane_value, scope)

    if all(isinstance(value, list) for value in (baseline, current, lane_value)) and (
        len(baseline) == len(current) == len(lane_value)
    ):
        return _merge_sequence_delta(baseline, current, lane_value, scope)

    source_path, source_line = scope.source_key
    raise GateError(
        f"lane {scope.transform!r} conflicts with an earlier lane at "
        f"{source_path}:{source_line}{_json_pointer(scope.path)}"
    )


def _merge_sequence_delta(
    baseline: list[Any],
    current: list[Any],
    lane_value: list[Any],
    scope: MergeScope,
) -> list[Any]:
    """Merge three equal-length lists position by position."""
    return [
        _merge_lane_delta(base_child, current[index], lane_value[index], scope.at(index))
        for index, base_child in enumerate(baseline)
    ]


def _merge_object_delta(
    baseline: dict[str, Any],
    current: dict[str, Any],
    lane_value: dict[str, Any],
    scope: MergeScope,
) -> dict[str, Any]:
    """Merge three objects member by member; members the lane left alone stay composed."""
    merged = copy.deepcopy(current)
    for key in sorted(set(baseline) | set(lane_value)):
        base_child = baseline.get(key, _MISSING)
        lane_child = lane_value.get(key, _MISSING)
        if _same_json(base_child, lane_child):
            continue
        current_child = current.get(key, _MISSING)
        result = _merge_lane_delta(base_child, current_child, lane_child, scope.at(key))
        if result is _MISSING:
            merged.pop(key, None)
        else:
            merged[key] = result
    return merged


if __package__:
    _expose_package_sibling(__name__)
