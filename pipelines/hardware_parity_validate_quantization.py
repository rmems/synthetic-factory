#!/usr/bin/env python3
"""Re-deriving the Q8.8 conversion from the scenario's float model.

Every per-parameter float, raw, dequantized and error value is recomputed from
`scenario.model_float` rather than trusted, so a record cannot describe a
quantization its own model does not produce.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))
from neuro_oracle import (  # noqa: E402
    Q88_MAX_RAW,
    Q88_MIN_RAW,
    q88_to_float,
    quantize_model,
)
from hardware_parity_terms import contract  # noqa: E402
from hardware_parity_validate_equality import _metrics_equal  # noqa: E402


def _check_quantization(record, where):
    """Re-derive the Q8.8 conversion from the float model and compare."""
    deployment = (record.get("oracle") or {}).get("deployment")
    if not isinstance(deployment, dict):
        return []
    recorded = deployment.get("quantization")
    model = (record.get("scenario") or {}).get("model_float")
    if not recorded:
        return [
            f"{where}: deployment side reports no Q8.8 conversion provenance "
            "[Q88_PROVENANCE_MISSING]"
        ]
    if not isinstance(model, dict):
        return [f"{where}: scenario.model_float missing [Q88_PROVENANCE_MISSING]"]
    for key in ("format", "fractional_bits", "rounding", "saturation_policy"):
        if key not in recorded:
            return [
                f"{where}: quantization provenance missing {key!r} "
                "[Q88_PROVENANCE_MISSING]"
            ]
    if recorded.get("fractional_bits") != 8 or recorded.get("format") != "Q8.8":
        return [
            f"{where}: quantization provenance is not Q8.8 [Q88_PROVENANCE_MISMATCH]"
        ]
    try:
        _, recomputed = quantize_model(model)
    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        OverflowError,
    ) as exc:
        return [f"{where}: scenario.model_float is not simulable: {exc}"]
    errors = _metrics_equal(
        recorded,
        recomputed,
        "oracle.deployment.quantization",
        where,
    )
    return [
        error.replace("[PARITY_METRIC_MISMATCH]", "[Q88_PROVENANCE_MISMATCH]")
        for error in errors
    ]


def _matrix_cell_valid(cell, binary, integer):
    """Exact-typed cell domains: `bool` never impersonates an int."""
    if binary:
        return type(cell) is int and cell in (0, 1)
    if integer:
        return type(cell) is int
    return type(cell) in (int, float) and (type(cell) is int or math.isfinite(cell))


def _matrix_cell_domain(binary, integer):
    if binary:
        return "an exact integer 0 or 1"
    if integer:
        return "an exact integer"
    return "a finite JSON number"


def _matrix_row_errors(row, row_index, columns, path, where, binary, integer):
    """One row's shape and cell-domain findings."""
    if not isinstance(row, list) or len(row) != columns:
        observed = len(row) if isinstance(row, list) else None
        return [
            f"{where}: {path}[{row_index}] must have exactly {columns} cells, "
            f"got {observed!r} [ENVELOPE_MALFORMED]"
        ]
    return [
        f"{where}: {path}[{row_index}][{column_index}] must be "
        f"{_matrix_cell_domain(binary, integer)}, got {cell!r} "
        "[ENVELOPE_MALFORMED]"
        for column_index, cell in enumerate(row)
        if not _matrix_cell_valid(cell, binary, integer)
    ]


def _matrix_errors(value, rows, columns, path, where, *, binary=False, integer=False):
    if not isinstance(value, list) or len(value) != rows:
        observed = len(value) if isinstance(value, list) else None
        return [
            f"{where}: {path} must have exactly {rows} rows, got {observed!r} "
            "[ENVELOPE_MALFORMED]"
        ]
    errors = []
    for row_index, row in enumerate(value):
        errors += _matrix_row_errors(
            row, row_index, columns, path, where, binary, integer
        )
    return errors


def _q88_raw_correspondence_errors(trace, raw, path, where):
    """Bind float membrane traces to signed Q8.8 integers."""
    errors = []
    for row_index, (trace_row, raw_row) in enumerate(zip(trace, raw)):
        for column_index, (value, raw_value) in enumerate(zip(trace_row, raw_row)):
            cell = f"{path}.trace_q88_raw[{row_index}][{column_index}]"
            if raw_value < Q88_MIN_RAW or raw_value > Q88_MAX_RAW:
                errors.append(
                    f"{where}: {cell} is outside the signed Q8.8 int16 range "
                    f"[{Q88_MIN_RAW}, {Q88_MAX_RAW}] [Q88_PROVENANCE_MISMATCH]"
                )
                continue
            expected = q88_to_float(raw_value)
            if not contract.strict_json_equal(value, expected):
                errors.append(
                    f"{where}: {path}.trace[{row_index}][{column_index}] is not "
                    "raw/256 of the retained Q8.8 integer [Q88_PROVENANCE_MISMATCH]"
                )
    return errors
