#!/usr/bin/env python3
"""Running one scenario on one runtime.

The only place that turns an interpreter outcome or exception into an
`executed` / `unsupported` / `unavailable` entry, so the three cannot drift
apart.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from neuro_oracle import digest  # noqa: E402
from nir_equivalence_graph import GraphError  # noqa: E402
from nir_equivalence_runtimes import (  # noqa: E402
    RuntimeUnavailable,
    UnsupportedConstruct,
)
from nir_equivalence_terms import (  # noqa: E402
    STATUS_EXECUTED,
    STATUS_UNAVAILABLE,
    STATUS_UNSUPPORTED,
)


def execute_runtime(runtime, scenario):
    """Run one runtime and return its entry, executed or not."""
    entry = {
        "runtime": runtime.name,
        "runtime_class": runtime.runtime_class,
        "conventions": dict(getattr(runtime, "conventions", {})),
        "supported_types": list(getattr(runtime, "supported_types", ())),
        "status": None,
    }
    status = runtime.availability()
    if not status["available"]:
        entry["status"] = STATUS_UNAVAILABLE
        entry["reason_code"] = status["reason_code"]
        entry["detail"] = status["detail"]
        return entry
    # Parse/write evidence belongs to the runtime adapter that performed it.
    # A module-level JSON round trip copied onto every entry would agree by
    # construction while proving nothing about either runtime boundary.
    entry["roundtrip"] = runtime.roundtrip_graph(scenario["graph"])
    try:
        outputs = runtime.execute(scenario["graph"], scenario["stimulus"])
    except UnsupportedConstruct as exc:
        entry["status"] = STATUS_UNSUPPORTED
        entry["reason_code"] = "UNSUPPORTED_CONSTRUCT"
        entry["detail"] = exc.detail
        entry["unsupported_node"] = exc.node
        entry["unsupported_type"] = exc.node_type
        return entry
    except (GraphError, RuntimeUnavailable) as exc:
        entry["status"] = STATUS_UNAVAILABLE
        entry["reason_code"] = getattr(exc, "reason_code", "RUNTIME_GRAPH_ERROR")
        entry["detail"] = str(exc)
        return entry
    entry["status"] = STATUS_EXECUTED
    entry["outputs"] = outputs
    # The digest covers the complete retained outputs object. `final_membrane`
    # and `recurrent_edges` feed the persisted comparison and attribution, so
    # a digest of only trace+events would let two observations that differ in
    # internal state share an identity -- and `result.derived_from` could no
    # longer name the complete evidence behind a DIVERGENCE_INTERNAL_STATE.
    entry["output_digest"] = digest(outputs)
    return entry


def _executed(entries):
    return [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("status") == STATUS_EXECUTED
    ]
