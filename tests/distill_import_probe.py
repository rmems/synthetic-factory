#!/usr/bin/env python3
"""Import-form probe for the distillation contract, run in a fresh interpreter.

:func:`run_form` executes in a child process started with the ``spawn``
method, so the interpreter it runs in has imported nothing of the contract.
It forgets any copy the child may have inherited on start-up anyway, puts
``sys.path`` the way the form under test would, imports in the order the form
names, and reports what it found as plain data: no code string crosses the
process boundary, and nothing here reaches for an import by computed name.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"

CONTRACT_SIBLINGS = (
    "import_twins",
    "distill_vocabulary",
    "distill_builders",
    "distill_measurements",
    "distill_energy_claims",
    "distill_blocks",
    "distill_curation",
    "distill_jsonl",
    "distill_labels",
)
# The fault-recovery family (F1): its root binds these eight siblings.
FAULT_SIBLINGS = (
    "fault_vocabulary",
    "fault_config",
    "fault_parameters",
    "fault_scenario",
    "fault_boundary",
    "fault_tiers",
    "fault_simulator",
    "fault_oracle",
)
SIBLINGS = CONTRACT_SIBLINGS + FAULT_SIBLINGS


def _forget_repository_modules() -> None:
    """Drop every module loaded from this repository, except the probe itself."""

    for name, module in list(sys.modules.items()):
        location = getattr(module, "__file__", None) or ""
        if name != __name__ and location.startswith(str(REPO)):
            del sys.modules[name]
    sys.path[:] = [entry for entry in sys.path if Path(entry or ".").resolve() not in (REPO, PIPELINES)]


def _cli_form() -> Any:
    """``python3 pipelines/x.py`` puts ``pipelines/`` first and imports flat."""

    sys.path.insert(0, str(PIPELINES))
    from oracle_grounded import distill_contract as flat
    importlib.import_module("oracle_grounded.fault_oracle")  # the family root binds its siblings

    return flat


def _package_form() -> tuple[Any, Any]:
    """``from pipelines import ...`` from the repository root, both spellings."""

    sys.path.insert(0, str(REPO))
    import pipelines.oracle_grounded.distill_contract as packaged
    importlib.import_module("pipelines.oracle_grounded.fault_oracle")
    from pipelines.oracle_grounded import distill_contract as packaged_again

    return packaged, packaged_again


def _siblings_split() -> list[str]:
    """The siblings whose two spellings are not one module object."""

    split = []
    for name in SIBLINGS:
        flat = sys.modules.get(f"oracle_grounded.{name}")
        packaged = sys.modules.get(f"pipelines.oracle_grounded.{name}")
        if flat is None or flat is not packaged:
            split.append(name)
    return split


def run_form(form: str) -> dict[str, Any]:
    """Run one import form in this (fresh) interpreter and report what it bound."""

    _forget_repository_modules()
    if form == "cli":
        flat = _cli_form()
        return {"schema_version": flat.SCHEMA_VERSION}
    if form == "package":
        packaged, packaged_again = _package_form()
        return {"one_object": packaged is packaged_again}
    first, second = form.split("_then_")
    if first == "package":
        packaged, packaged_again = _package_form()
        flat = _cli_form()
    else:
        flat = _cli_form()
        packaged, packaged_again = _package_form()
    return {
        "one_object": packaged is flat and packaged_again is packaged,
        "one_error_class": packaged.ContractError is flat.ContractError,
        "split_siblings": _siblings_split(),
        "order": (first, second),
    }
