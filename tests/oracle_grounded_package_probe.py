#!/usr/bin/env python3
"""Import-form probe for the ``oracle_grounded`` package, run in a fresh interpreter.

Mirrors ``distill_import_probe``: a spawned child forgets every repository
module, puts ``sys.path`` the way one import form would, imports the package
itself (not a sibling) in that form's order, and reports what it bound as
plain data. The package-only order is the one ``__init__.py`` has to bind;
sibling imports already bind the parent as a side effect.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
# Reserved names with no backing submodule. The six names main once carried here
# (canon, families, generators, oracles, record, sim) graduated to real
# submodules when the oracle-grounded family stack landed, so none remain.
# Keep the machinery: a future reserved name is re-added here and stays pinned
# absent until its module lands.
PHANTOM_NAMES: tuple[str, ...] = ()
DECLARED_NAMES = ("refusals", "rng")
FLAT_NAME = "oracle_grounded"
PACKAGED_NAME = f"pipelines.{FLAT_NAME}"


def _forget_repository_modules() -> None:
    """Drop every module loaded from this repository, except the probe itself."""

    for name, module in list(sys.modules.items()):
        location = getattr(module, "__file__", None) or ""
        if name != __name__ and location.startswith(str(REPO)):
            del sys.modules[name]
    sys.path[:] = [
        entry
        for entry in sys.path
        if Path(entry or ".").resolve() not in (REPO, PIPELINES)
    ]


def _cli_form() -> Any:
    """``python3 pipelines/x.py`` puts ``pipelines/`` first and imports flat."""

    sys.path.insert(0, str(PIPELINES))
    import oracle_grounded as flat

    return flat


def _package_form() -> Any:
    """``from pipelines import ...`` from the repository root."""

    sys.path.insert(0, str(REPO))
    import pipelines.oracle_grounded as packaged

    return packaged


def _phantom_outcomes(package_name: str) -> dict[str, str]:
    """Each reserved phantom name resolves to nothing; none become a success.

    ``find_spec`` answers existence without executing the module, which is what
    this assertion is actually about. Importing a name to prove it is absent
    runs arbitrary module code on every name that turns out to be present.
    """

    outcomes = {}
    for name in PHANTOM_NAMES:
        try:
            spec = importlib.util.find_spec(f"{package_name}.{name}")
        except ModuleNotFoundError:
            outcomes[name] = "absent"
        else:
            outcomes[name] = "present" if spec is not None else "absent"
    return outcomes


def _seed_outcome(rng_module: Any, error_type: type[BaseException]) -> str:
    """A domain refusal stays a contract error, never a successful stream."""

    try:
        rng_module.DrawStream(-1)
    except error_type:
        return "contract_error"
    except Exception as exc:
        return type(exc).__name__
    return "succeeded"


def _undeclared_code_outcome(refusals_module: Any) -> str:
    """An undeclared finding code is a LookupError, not a coded refusal."""

    try:
        refusals_module.CodedRefusal("NOT_A_CODE", "x")
    except LookupError:
        return "lookup_error"
    except Exception as exc:
        return type(exc).__name__
    return "succeeded"


def _dotted_attribute_chain() -> str:
    """A bare dotted import must leave ``pipelines.oracle_grounded`` reachable.

    ``importlib.import_module`` and ``import ... as ...`` both return the module
    directly, so neither walks the parent attribute chain. Only a bare
    ``import pipelines.oracle_grounded.rng`` does, and that is the form that
    breaks when the CLI spelling loaded first and the parent package never had
    the child bound onto it.
    """

    try:
        import pipelines.oracle_grounded.rng

        return pipelines.oracle_grounded.rng.__name__
    except AttributeError as exc:
        return f"AttributeError: {exc}"


def run_form(form: str) -> dict[str, Any]:
    """Run one import form in this (fresh) interpreter and report what it bound."""

    _forget_repository_modules()
    if form == "cli":
        pkg = _cli_form()
        return {
            "all": list(pkg.__all__),
            "twin_bound": sys.modules.get(PACKAGED_NAME) is pkg,
            "phantoms": _phantom_outcomes(FLAT_NAME),
        }
    if form == "package":
        pkg = _package_form()
        return {
            "all": list(pkg.__all__),
            "twin_bound": sys.modules.get(FLAT_NAME) is pkg,
            "phantoms": _phantom_outcomes(PACKAGED_NAME),
        }
    first, _sep, second = form.partition("_then_")
    loaders = {"cli": _cli_form, "package": _package_form}
    one, two = loaders[first](), loaders[second]()
    flat = sys.modules[FLAT_NAME]
    packaged = sys.modules[PACKAGED_NAME]
    refusals = importlib.import_module(f"{FLAT_NAME}.refusals")
    packaged_refusals = importlib.import_module(f"{PACKAGED_NAME}.refusals")
    rng = importlib.import_module(f"{FLAT_NAME}.rng")
    envelope = importlib.import_module(f"{FLAT_NAME}.envelope")
    packaged_envelope = importlib.import_module(f"{PACKAGED_NAME}.envelope")
    try:
        packaged_rng = importlib.import_module(f"{PACKAGED_NAME}.rng")
        packaged_rng.DrawStream(-1)
        packaged_seed = "succeeded"
    except envelope.ContractError:
        packaged_seed = "caught_through_flat"
    except Exception as exc:
        packaged_seed = type(exc).__name__
    return {
        "one_object": one is two is flat is packaged,
        "one_refusal_class": refusals.CodedRefusal is packaged_refusals.CodedRefusal,
        "one_contract_error": envelope.ContractError is packaged_envelope.ContractError,
        "seed_outcome": _seed_outcome(rng, envelope.ContractError),
        "packaged_seed_caught_through_flat": packaged_seed,
        "dotted_attribute_chain": _dotted_attribute_chain(),
        "undeclared_code": _undeclared_code_outcome(refusals),
        "all": list(one.__all__),
        # The two declared names are already resolved above, so assert against
        # those objects rather than importing them a second time by name.
        "declared_bound": {
            "refusals": getattr(flat, "refusals") is refusals,
            "rng": getattr(flat, "rng") is rng,
        },
    }
