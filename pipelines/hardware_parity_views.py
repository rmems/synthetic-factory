#!/usr/bin/env python3
"""Training-view projection.

A view cannot drop, soften or relabel a parity failure, and a view set that
does not cover the catalog fails authentication rather than passing quietly.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_views")
    from .hardware_parity_terms import (  # noqa: E402
        VALIDATION_DATA_ERRORS,
        contract,
    )
    from .hardware_parity_catalog import SCENARIO_SPECS  # noqa: E402
    from .hardware_parity_record import _expected_summary  # noqa: E402
    from .hardware_parity_validate_result import validate_records  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_views"
    )
    from hardware_parity_terms import (  # noqa: E402
        VALIDATION_DATA_ERRORS,
        contract,
    )
    from hardware_parity_catalog import SCENARIO_SPECS  # noqa: E402
    from hardware_parity_record import _expected_summary  # noqa: E402
    from hardware_parity_validate_result import validate_records  # noqa: E402

def training_view(record):
    """A supervised view that carries the parity verdict on its face."""
    scenario = record.get("scenario") or {}
    oracle = record.get("oracle") or {}
    targets = [
        side.get("execution_target")
        for side in (oracle.get("software"), oracle.get("deployment"))
        if isinstance(side, dict)
    ]
    deployment = oracle.get("deployment")
    fixture_sha = (scenario.get("input_fixture") or {}).get("sha256")
    prompt = _view_prompt(scenario, oracle, deployment, fixture_sha)
    completion = _expected_summary(record)
    view = contract.build_training_view(record, prompt, completion, targets)
    view["stress"] = scenario.get("stress")
    view["scenario_id"] = scenario.get("id")
    return view


def _view_prompt(scenario, oracle, deployment, fixture_sha):
    """The claim prompt for the record's oracle shape."""
    if isinstance(deployment, dict) and "capture" in deployment:
        return (
            f"A recorded trace claims deployment target {deployment.get('execution_target')!r} "
            f"for scenario {scenario.get('name')!r} and encoded input fixture {fixture_sha}. "
            "Its physical execution is unverified. What do the retained traces establish?"
        )
    if isinstance(deployment, dict):
        return (
            f"A Spikenaut network ({scenario.get('name')}) is exported to Q8.8 and "
            f"executed on the deployment target under stress {scenario.get('stress')!r}. "
            f"Identical encoded input fixture {fixture_sha}. Does the behaviour survive "
            "the export?"
        )
    requested = (oracle.get("requested_deployment") or {}).get("adapter")
    return (
        f"A Spikenaut network ({scenario.get('name')}) executed only on the software "
        f"reference under stress {scenario.get('stress')!r}, using encoded input "
        f"fixture {fixture_sha}. Requested deployment adapter {requested!r} did not "
        "execute. Is paired deployment parity established?"
    )


def training_view_errors(record, view, where):
    """Authenticate the complete hardware-parity training projection."""
    errors = contract.training_view_errors(record, view, where)
    try:
        expected = training_view(record)
    except VALIDATION_DATA_ERRORS as exc:
        return errors + [
            f"{where}: cannot rederive the hardware training view: {exc} "
            "[TRAINING_VIEW_HIDES_FAILURE]"
        ]
    if not contract.strict_json_equal(view, expected):
        errors.append(
            f"{where}: training view must exactly match the validator-derived "
            "hardware projection [TRAINING_VIEW_HIDES_FAILURE]"
        )
    return errors


def build_training_views(records, source="record"):
    """Build views for every record and prove none of them softened a failure."""
    validation_errors = validate_records(records, source=source)
    if validation_errors:
        return [], validation_errors
    # Authenticate the batch against the fixed scenario catalog before
    # projecting it: a pre-filtered input would otherwise pass every view/set
    # check against its own subset while silently dropping the failures the
    # round produced. Runs after per-record validation, which bound each
    # scenario id and round to its own evidence.
    errors = contract.catalog_batch_errors(
        records, [spec["id"] for spec in SCENARIO_SPECS], source
    )
    views = [training_view(record) for record in records]
    for index, (record, view) in enumerate(zip(records, views), 1):
        errors += training_view_errors(record, view, f"{source}:{index}")
    errors += contract.view_set_errors(records, views, source)
    return views, errors


if __package__:
    _expose_package_sibling(__name__)
