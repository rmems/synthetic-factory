#!/usr/bin/env python3
"""Training-view projection.

A view cannot drop, soften or relabel a divergence, and the prompt cannot
invent a runtime pair the record does not carry.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from nir_equivalence_base import (  # noqa: E402
    _safe_digest,
    _strict_json_equal,
)
from nir_equivalence_catalog import (  # noqa: E402
    _GRAPH_CATALOG_BY_ID,
    _catalog_entry,
    _catalog_stimulus,
)
from nir_equivalence_compare import _summarize  # noqa: E402
from nir_equivalence_terms import (  # noqa: E402
    VALIDATION_DATA_ERRORS,
    contract,
)
from nir_equivalence_validate_result import validate_records  # noqa: E402


def _catalog_prompt_identity(scenario):
    """Return prompt identity from the catalog, never mutable record prose."""
    scenario_id = scenario.get("id") if isinstance(scenario, dict) else None
    catalog = _catalog_entry(scenario_id)
    if catalog is None:
        return {
            "name": scenario.get("name") if isinstance(scenario, dict) else None,
            "class": scenario.get("class") if isinstance(scenario, dict) else None,
            "fixture_sha256": None,
        }
    stimulus = scenario.get("stimulus")
    steps = stimulus.get("steps") if isinstance(stimulus, dict) else None
    expected_stimulus = _catalog_stimulus(scenario_id, steps)
    fixture_sha256 = (
        _safe_digest(expected_stimulus["events"])
        if isinstance(expected_stimulus, dict)
        else None
    )
    return {
        "name": catalog["name"],
        "class": catalog["class"],
        "fixture_sha256": fixture_sha256,
    }


def training_view(record):
    scenario = record.get("scenario") or {}
    result = record.get("result") or {}
    oracle = record.get("oracle") or {}
    runtimes = oracle.get("runtimes") or []
    targets = [
        f"{entry.get('runtime')}:{entry.get('status')}"
        for entry in runtimes
        if isinstance(entry, dict)
    ]
    executed = list((result.get("comparison") or {}).get("executed_runtimes") or [])
    if len(executed) >= 2:
        execution_claim = f"was executed across runtimes {executed!r}"
    elif len(executed) == 1:
        execution_claim = f"executed on only one runtime, {executed[0]!r}"
    else:
        execution_claim = "did not execute on any runtime"
    prompt_identity = _catalog_prompt_identity(scenario)
    prompt = (
        f"NIR graph '{prompt_identity['name']}' (class {prompt_identity['class']}) "
        f"{execution_claim} against stimulus "
        f"{prompt_identity['fixture_sha256']}. "
        "What does the available evidence establish about runtime equivalence?"
    )
    catalog_scenario = dict(scenario) if isinstance(scenario, dict) else {}
    catalog_scenario["name"] = prompt_identity["name"]
    catalog_scenario["class"] = prompt_identity["class"]
    completion = _summarize(
        catalog_scenario,
        result.get("comparison") or {},
        result.get("verdict"),
    )
    view = contract.build_training_view(record, prompt, completion, targets)
    view["graph_class"] = prompt_identity["class"]
    view["scenario_id"] = scenario.get("id")
    view["executed_runtimes"] = list(
        (result.get("comparison") or {}).get("executed_runtimes") or []
    )
    view["evidence_scope"] = oracle.get("evidence_scope")
    return view


def training_view_errors(record, view, where):
    """Authenticate the complete NIR projection, including family fields."""
    errors = contract.training_view_errors(record, view, where)
    try:
        expected = training_view(record)
    except VALIDATION_DATA_ERRORS as exc:
        return errors + [
            f"{where}: cannot rederive the NIR training view: {exc} "
            "[TRAINING_VIEW_HIDES_FAILURE]"
        ]
    if not _strict_json_equal(view, expected):
        errors.append(
            f"{where}: training view must exactly match the validator-derived NIR "
            "projection [TRAINING_VIEW_HIDES_FAILURE]"
        )
    return errors


def build_training_views(records, source="record"):
    validation_errors = validate_records(records, source=source)
    if validation_errors:
        return [], validation_errors
    # Authenticate the batch against the fixed graph catalog before
    # projecting it: a pre-filtered input would otherwise pass every view/set
    # check against its own subset while silently dropping the divergences
    # the round produced. Runs after per-record validation, which bound each
    # scenario id and round to its own evidence.
    errors = contract.catalog_batch_errors(
        records, list(_GRAPH_CATALOG_BY_ID), source
    )
    views = [training_view(record) for record in records]
    for index, (record, view) in enumerate(zip(records, views), 1):
        errors += training_view_errors(record, view, f"{source}:{index}")
    errors += contract.view_set_errors(records, views, source)
    return views, errors
