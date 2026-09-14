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
    entries = []
    saturated_count = 0

    def _convert(path, value):
        nonlocal saturated_count
        raw, saturated = q88_quantize(value)
        if saturated:
            saturated_count += 1
        entries.append(
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

    q_model = {
        "name": model["name"],
        "neurons": model["neurons"],
        "inputs": model["inputs"],
        "refractory_steps": model["refractory_steps"],
        "reset": model["reset"],
        "dt_ms": model["dt_ms"],
        "w_in": [
            [_convert(f"w_in[{i}][{j}]", cell) for j, cell in enumerate(row)]
            for i, row in enumerate(model["w_in"])
        ],
        "w_rec": (
            [
                [_convert(f"w_rec[{i}][{j}]", cell) for j, cell in enumerate(row)]
                for i, row in enumerate(model["w_rec"])
            ]
            if model["w_rec"] is not None
            else None
        ),
        "bias": [_convert(f"bias[{i}]", cell) for i, cell in enumerate(model["bias"])],
        "threshold": [
            _convert(f"threshold[{i}]", cell) for i, cell in enumerate(model["threshold"])
        ],
        "decay": [_convert(f"decay[{i}]", cell) for i, cell in enumerate(model["decay"])],
        "action_labels": list(model["action_labels"]),
    }
    errors = [entry["abs_error"] for entry in entries]
    provenance = {
        "format": "Q8.8",
        "signed": True,
        "total_bits": 16,
        "fractional_bits": Q88_FRACTIONAL_BITS,
        "step": Q88_STEP,
        "representable_range": [Q88_MIN_VALUE, Q88_MAX_VALUE],
        "rounding": Q88_ROUNDING,
        "saturation_policy": Q88_SATURATION_POLICY,
        "units": {"weights": "dimensionless", "threshold": "mV_model", "decay": "ratio"},
        "parameters": entries,
        "parameter_count": len(entries),
        "saturated_parameter_count": saturated_count,
        "max_abs_error": max(errors) if errors else 0.0,
        "mean_abs_error": (sum(errors) / len(errors)) if errors else 0.0,
        "source_model_sha256": digest(model),
    }
    return q_model, provenance


if __package__:
    _expose_package_sibling(__name__)
