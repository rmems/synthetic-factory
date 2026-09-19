#!/usr/bin/env python3
"""Q8.8 conversion provenance: every parameter's float, raw, dequantized value
and error.

Recorded per parameter rather than summarized, because the validator
re-derives the whole conversion from `scenario.model_float` and compares.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("neuro_oracle_quantize")
    from .neuro_oracle_digest import digest  # noqa: E402
    from .neuro_oracle_model import normalize_model  # noqa: E402
    from .neuro_oracle_q88 import (  # noqa: E402
        Q88_FRACTIONAL_BITS,
        Q88_MAX_VALUE,
        Q88_MIN_VALUE,
        Q88_ROUNDING,
        Q88_SATURATION_POLICY,
        Q88_STEP,
        q88_quantize,
        q88_to_float,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "neuro_oracle_quantize"
    )
    from neuro_oracle_digest import digest  # noqa: E402
    from neuro_oracle_model import normalize_model  # noqa: E402
    from neuro_oracle_q88 import (  # noqa: E402
        Q88_FRACTIONAL_BITS,
        Q88_MAX_VALUE,
        Q88_MIN_VALUE,
        Q88_ROUNDING,
        Q88_SATURATION_POLICY,
        Q88_STEP,
        q88_quantize,
        q88_to_float,
    )

def quantize_model(model):
    """Quantize a float model to Q8.8 and record full conversion provenance.

    Returns ``(q_model, provenance)``. ``q_model`` carries raw integers;
    ``provenance`` carries, for every scalar, the float source, the raw
    integer, the dequantized value, the absolute error, and whether the
    conversion saturated. Nothing about the conversion is left implicit.
    """
    model = normalize_model(model)
    tape = _QuantizeTape()
    q_model = _quantized_fields(model, tape.convert)
    return q_model, _quantization_provenance(model, tape)


class _QuantizeTape:
    """Accumulates one provenance entry per converted scalar."""

    def __init__(self):
        self.entries = []
        self.saturated_count = 0

    def convert(self, path, value):
        raw, saturated = q88_quantize(value)
        if saturated:
            self.saturated_count += 1
        self.entries.append(
            {
                "parameter": path,
                "float": value,
                "q88_raw": raw,
                "q88_value": q88_to_float(raw),
                "abs_error": abs(value - q88_to_float(raw)),
                "saturated": saturated,
            }
        )
        return raw


def _quantized_fields(model, convert):
    """Every model field, routed through ``convert`` so each scalar is taped."""
    return {
        "name": model["name"],
        "neurons": model["neurons"],
        "inputs": model["inputs"],
        "refractory_steps": model["refractory_steps"],
        "reset": model["reset"],
        "dt_ms": model["dt_ms"],
        "w_in": _quantized_matrix("w_in", model["w_in"], convert),
        "w_rec": (
            _quantized_matrix("w_rec", model["w_rec"], convert)
            if model["w_rec"] is not None
            else None
        ),
        "bias": _quantized_vector("bias", model["bias"], convert),
        "threshold": _quantized_vector(
            "threshold", model["threshold"], convert
        ),
        "decay": _quantized_vector("decay", model["decay"], convert),
        "action_labels": list(model["action_labels"]),
    }


def _quantized_matrix(path, rows, convert):
    """A 2-D weight block with per-cell provenance paths."""
    return [
        [convert(f"{path}[{i}][{j}]", cell) for j, cell in enumerate(row)]
        for i, row in enumerate(rows)
    ]


def _quantized_vector(path, values, convert):
    """A 1-D parameter block with per-cell provenance paths."""
    return [convert(f"{path}[{i}]", cell) for i, cell in enumerate(values)]


def _quantization_provenance(model, tape):
    """The per-scalar conversion ledger plus aggregate error statistics."""
    errors = [entry["abs_error"] for entry in tape.entries]
    return {
        "format": "Q8.8",
        "signed": True,
        "total_bits": 16,
        "fractional_bits": Q88_FRACTIONAL_BITS,
        "step": Q88_STEP,
        "representable_range": [Q88_MIN_VALUE, Q88_MAX_VALUE],
        "rounding": Q88_ROUNDING,
        "saturation_policy": Q88_SATURATION_POLICY,
        "units": {"weights": "dimensionless", "threshold": "mV_model", "decay": "ratio"},
        "parameters": tape.entries,
        "parameter_count": len(tape.entries),
        "saturated_parameter_count": tape.saturated_count,
        "max_abs_error": max(errors) if errors else 0.0,
        "mean_abs_error": (sum(errors) / len(errors)) if errors else 0.0,
        "source_model_sha256": digest(model),
    }


if __package__:
    _expose_package_sibling(__name__)
