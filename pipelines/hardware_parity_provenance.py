#!/usr/bin/env python3
"""The generator's own identity: the family source digest and the catalog stamps.

Every record carries these, and the validator re-derives them from here, so this
is the one module whose output binds a record to the code that produced it.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))
from neuro_oracle import digest  # noqa: E402
from hardware_parity_terms import (  # noqa: E402
    CATALOG_AUTHORSHIP,
    FACTORY_SLUG,
    GENERATOR_BLOCK,
    VALIDATOR,
)
from hardware_parity_catalog import build_scenarios  # noqa: E402


_FAMILY = (
    "hardware_parity.py",
    "hardware_parity_catalog.py",
    "hardware_parity_cli.py",
    "hardware_parity_metrics.py",
    "hardware_parity_provenance.py",
    "hardware_parity_record.py",
    "hardware_parity_terms.py",
    "hardware_parity_validate_capture.py",
    "hardware_parity_validate_deployment.py",
    "hardware_parity_validate_equality.py",
    "hardware_parity_validate_identity.py",
    "hardware_parity_validate_observation.py",
    "hardware_parity_validate_oracle.py",
    "hardware_parity_validate_quantization.py",
    "hardware_parity_validate_result.py",
    "hardware_parity_views.py",
)


def _family_sources():
    """The family's source texts by path, or raise if the directory disagrees."""
    found = tuple(sorted(path.name for path in _PIPELINES.glob("hardware_parity*.py")))
    if found != tuple(sorted(_FAMILY)):
        raise RuntimeError(
            f"{VALIDATOR}: the hardware_parity family on disk is {found}, but "
            f"_FAMILY declares {tuple(sorted(_FAMILY))}. generator_version must "
            "cover every file that generates, so reconcile the two before running."
        )
    return [
        {"path": f"pipelines/{name}", "text": (_PIPELINES / name).read_text(encoding="utf-8")}
        for name in sorted(_FAMILY)
    ]


def _module_source_digest():
    """Immutable source digest of the whole family, used as the generator_version.

    The family, not this file. The generator was one module and is now several
    siblings; a digest over only this one would stop attesting the code that
    actually builds records, which is the opposite of what the stamp is for.
    """
    return digest({"paths": _family_sources()})

def _catalog_digest():
    """Digest of the scenario catalog identity (ids + models + stresses)."""
    catalog = [
        {
            "id": scenario["id"],
            "name": scenario["name"],
            "family": scenario["family"],
            "stress": scenario["stress"],
            "model_float": scenario["model_float"],
        }
        for scenario in build_scenarios(steps=12)
    ]
    return digest({"factory": FACTORY_SLUG, "catalog": catalog})


def _catalog_provenance_stamps():
    """generator / generator_version / catalog_digest / catalog_authorship."""
    return {
        "generator": GENERATOR_BLOCK["name"],
        "generator_version": _module_source_digest(),
        "catalog_digest": _catalog_digest(),
        "catalog_authorship": copy.deepcopy(CATALOG_AUTHORSHIP),
    }
