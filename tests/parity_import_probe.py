#!/usr/bin/env python3
"""Import-form probe for the parity families, run in a fresh interpreter.

Mirrors ``distill_import_probe``: :func:`run_form` executes in a child process
started with the ``spawn`` method, forgets any repository module the child
inherited, puts ``sys.path`` the way the form under test would, imports in the
order the form names, and reports plain data. No code string crosses the
process boundary and nothing here imports by computed name.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"

FACADES = ("hardware_parity", "nir_equivalence", "neuro_oracle")

# Every flat sibling of the three families, and the subpackage modules they
# reach through ``oracle_grounded``; each must be one object under both names.
FLAT_SIBLINGS = tuple(
    sorted(
        path.stem
        for path in PIPELINES.glob("*.py")
        if path.stem.startswith(FACADES)
    )
)
SUBPACKAGE_SIBLINGS = (
    "parity_blocks",
    "parity_contract",
    "parity_destination",
    "parity_envelope",
    "parity_history",
    "parity_jsonl",
    "parity_publication",
    "parity_terms",
    "parity_view_sets",
    "parity_views",
    "family_digest",
)

# The exception classes a caller catches by name; a split here means an error
# raised through one import name is not caught through the other.
ERROR_CLASSES = (
    ("neuro_oracle", "OracleUnavailable"),
    ("nir_equivalence", "GraphError"),
    ("nir_equivalence", "UnsupportedConstruct"),
    ("nir_equivalence", "RuntimeUnavailable"),
)


def _forget_repository_modules() -> None:
    """Drop every module loaded from this repository, except the probe itself."""

    stale = [
        name
        for name, module in sys.modules.items()
        if name != __name__ and (getattr(module, "__file__", None) or "").startswith(str(REPO))
    ]
    for name in stale:
        del sys.modules[name]
    keep = (REPO, PIPELINES)
    sys.path[:] = [entry for entry in sys.path
                   if Path(entry or ".").resolve() not in keep]


def _cli_form() -> dict[str, Any]:
    """``python3 pipelines/x.py`` puts ``pipelines/`` first and imports flat."""

    sys.path.insert(0, str(PIPELINES))
    import hardware_parity
    import neuro_oracle
    import nir_equivalence
    from oracle_grounded import parity_publication  # noqa: F401 - import identity probe

    return {
        "hardware_parity": hardware_parity,
        "nir_equivalence": nir_equivalence,
        "neuro_oracle": neuro_oracle,
    }


def _package_form() -> dict[str, Any]:
    """``from pipelines import ...`` from the repository root."""

    sys.path.insert(0, str(REPO))
    from pipelines import hardware_parity, neuro_oracle, nir_equivalence
    from pipelines.oracle_grounded import parity_publication  # noqa: F401 - import identity probe

    return {
        "hardware_parity": hardware_parity,
        "nir_equivalence": nir_equivalence,
        "neuro_oracle": neuro_oracle,
    }


def _split_siblings() -> list[str]:
    """The siblings whose two spellings are not one module object."""

    names = (*FLAT_SIBLINGS, *(f"oracle_grounded.{name}" for name in SUBPACKAGE_SIBLINGS))
    return [name for name in names if not _single_module(name)]


def _single_module(name: str) -> bool:
    module = sys.modules.get(name)
    return module is not None and module is sys.modules.get(f"pipelines.{name}")


def _one_error_class(flat: dict[str, Any], packaged: dict[str, Any]) -> dict[str, bool]:
    return {
        f"{facade}.{name}": getattr(flat[facade], name) is getattr(packaged[facade], name)
        for facade, name in ERROR_CLASSES
    }


def run_form(form: str) -> dict[str, Any]:
    """Run one import form in this (fresh) interpreter and report what it bound."""

    _forget_repository_modules()
    if form == "cli":
        flat = _cli_form()
        return {"facades": sorted(flat)}
    if form == "package":
        packaged = _package_form()
        return {"facades": sorted(packaged), "split_siblings": _split_siblings()}
    first, _second = form.split("_then_")
    forms = (("package", _package_form), ("cli", _cli_form))
    if first != "package":
        forms = forms[::-1]
    bound = {}
    for label, loader in forms:
        bound[label] = loader()
    return {
        "one_object": all(bound["cli"][f] is bound["package"][f] for f in FACADES),
        "one_error_class": _one_error_class(bound["cli"], bound["package"]),
        "split_siblings": _split_siblings(),
    }
