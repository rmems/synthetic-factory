#!/usr/bin/env python3
"""Re-executing the in-repo runtimes and comparing against what was recorded.

The anti-fabrication gate: recomputing a comparison from a record's own outputs
would accept a record whose two sides were copied from each other, so the
outputs themselves are re-derived.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_validate_replay")
    from .neuro_oracle import digest  # noqa: E402
    from .nir_equivalence_graph import GraphError  # noqa: E402
    from .nir_equivalence_runtimes import (  # noqa: E402
        UnsupportedConstruct,
        _RUNTIME_BY_NAME,
    )
    from .nir_equivalence_terms import (  # noqa: E402
        STATUS_EXECUTED,
        STATUS_UNSUPPORTED,
        contract,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_validate_replay"
    )
    from neuro_oracle import digest  # noqa: E402
    from nir_equivalence_graph import GraphError  # noqa: E402
    from nir_equivalence_runtimes import (  # noqa: E402
        UnsupportedConstruct,
        _RUNTIME_BY_NAME,
    )
    from nir_equivalence_terms import (  # noqa: E402
        STATUS_EXECUTED,
        STATUS_UNSUPPORTED,
        contract,
    )

def _reexecute_in_repo_runtimes(record, where):
    """Re-run every in-repo runtime and compare digests with what was recorded.

    This is the anti-fabrication gate for this family: an output trace that the
    interpreter does not reproduce cannot survive validation. Runtimes that are
    not in-repo cannot be re-executed here, and the record says so rather than
    pretending they were checked.
    """
    scenario = record.get("scenario") or {}
    graph = scenario.get("graph")
    stimulus = scenario.get("stimulus")
    if not isinstance(graph, dict) or not isinstance(stimulus, dict):
        return [f"{where}: scenario.graph and scenario.stimulus are required"]
    errors = []
    for entry in ((record.get("oracle") or {}).get("runtimes")) or []:
        runtime = _reexecutable_runtime(entry)
        if runtime is not None:
            label = f"{where}.oracle.runtimes[{entry.get('runtime')!r}]"
            errors += _replay_entry_errors(runtime, entry, scenario, label)
    return errors


def _reexecutable_runtime(entry):
    """The in-repo interpreter this entry names, or None when it names another.

    An entry naming a runtime this validator cannot re-execute is left to
    `_check_runtimes`, which is what refuses an unfalsifiable executed claim.
    """
    if not isinstance(entry, dict):
        return None
    runtime_name = entry.get("runtime")
    if not isinstance(runtime_name, str):
        return None
    return _RUNTIME_BY_NAME.get(runtime_name)


def _replay_entry_errors(runtime, entry, scenario, label):
    """Re-run one in-repo runtime and hold its entry to what actually came back.

    The caller has already established that `scenario` carries a graph and a
    stimulus object.
    """
    graph = scenario["graph"]
    try:
        outputs = runtime.execute(graph, scenario["stimulus"])
    except UnsupportedConstruct as exc:
        return _unsupported_replay_errors(entry, exc, label) + _roundtrip_replay_errors(
            runtime, entry, graph, label
        )
    except GraphError as exc:
        return [f"{label}: graph is not executable: {exc}"]
    except (
        KeyError,
        TypeError,
        ValueError,
        IndexError,
        AttributeError,
        OverflowError,
    ) as exc:
        return [f"{label}: scenario is not executable: {exc}"]
    if entry.get("status") != STATUS_EXECUTED:
        return [
            f"{label}: runtime executes this graph but the record says "
            f"{entry.get('status')!r} [RUNTIME_STATUS_UNKNOWN]"
        ]
    return _executed_replay_errors(entry, outputs, label) + _roundtrip_replay_errors(
        runtime, entry, graph, label
    )


def _unsupported_replay_errors(entry, exc, label):
    """A runtime that refuses the graph obliges the entry to say exactly that."""
    errors = []
    if entry.get("status") != STATUS_UNSUPPORTED:
        errors.append(
            f"{label}: runtime actually rejects this graph ({exc.node_type}) but "
            f"the record says {entry.get('status')!r} [UNSUPPORTED_NOT_DIAGNOSED]"
        )
    expected_diagnostic = {
        "reason_code": "UNSUPPORTED_CONSTRUCT",
        "unsupported_node": exc.node,
        "unsupported_type": exc.node_type,
        "detail": exc.detail,
    }
    errors += _diagnostic_field_errors(entry, expected_diagnostic, label)
    return errors


def _diagnostic_field_errors(entry, expected_diagnostic, label):
    errors = []
    for key, expected in expected_diagnostic.items():
        if entry.get(key) != expected:
            errors.append(
                f"{label}: {key} recorded {entry.get(key)!r} but the runtime "
                f"reported {expected!r} [UNSUPPORTED_NOT_DIAGNOSED]"
            )
    return errors


def _executed_replay_errors(entry, outputs, label):
    """An executed entry must carry exactly the outputs the re-execution produced."""
    errors = []
    if entry.get("output_digest") != digest(outputs):
        errors.append(
            f"{label}: recorded output digest does not match a re-execution "
            "[COMPARISON_MISMATCH]"
        )
    errors += _recorded_outputs_digest_errors(entry, label)
    if not contract.strict_json_equal(entry.get("outputs"), outputs):
        errors.append(
            f"{label}: recorded outputs do not match a re-execution under strict "
            "JSON numeric typing [COMPARISON_MISMATCH]"
        )
    return errors


def _recorded_outputs_digest_errors(entry, label):
    """The recorded digest must identify the recorded outputs, not just a re-run.

    The whole outputs object, not a trace+events subset: `spike_count`,
    `final_membrane`, and `recurrent_edges` also feed the comparison and
    attribution, so digesting a subset would leave the rest editable -- and
    editing them deletes divergence diagnostics from a family whose entire
    product is divergence.
    """
    recorded_outputs = entry.get("outputs")
    if not isinstance(recorded_outputs, dict):
        return []
    try:
        recorded_digest = digest(recorded_outputs)
    except (TypeError, ValueError, OverflowError) as exc:
        return [
            f"{label}: recorded outputs are not digestible: {exc} "
            "[COMPARISON_MISMATCH]"
        ]
    if entry.get("output_digest") != recorded_digest:
        return [
            f"{label}: output_digest does not identify the recorded outputs "
            "[COMPARISON_MISMATCH]"
        ]
    return []


def _roundtrip_replay_errors(runtime, entry, graph, label):
    """The recorded parse/write parity must match this runtime's own adapter."""
    fresh_roundtrip = runtime.roundtrip_graph(graph)
    if contract.strict_json_equal(entry.get("roundtrip"), fresh_roundtrip):
        return []
    return [
        f"{label}: recorded parse/write parity does not match this runtime's "
        "adapter [ROUNDTRIP_STRUCTURE_MISMATCH]"
    ]


if __package__:
    _expose_package_sibling(__name__)
