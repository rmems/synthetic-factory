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

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_provenance")
    from .oracle_grounded import family_digest  # noqa: E402
    from .neuro_oracle import digest  # noqa: E402
    from .hardware_parity_terms import (  # noqa: E402
        CATALOG_AUTHORSHIP,
        FACTORY_SLUG,
        GENERATOR_BLOCK,
        VALIDATOR,
    )
    from .hardware_parity_catalog import build_scenarios  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_provenance"
    )
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from oracle_grounded import family_digest  # noqa: E402
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
    "hardware_parity_metrics_spikes.py",
    "hardware_parity_provenance.py",
    "hardware_parity_record.py",
    "hardware_parity_terms.py",
    "hardware_parity_validate_availability.py",
    "hardware_parity_validate_capture.py",
    "hardware_parity_validate_deployment.py",
    "hardware_parity_validate_determinism.py",
    "hardware_parity_validate_equality.py",
    "hardware_parity_validate_identity.py",
    "hardware_parity_validate_observation.py",
    "hardware_parity_validate_oracle.py",
    "hardware_parity_validate_quantization.py",
    "hardware_parity_validate_result.py",
    "hardware_parity_views.py",
)


def _family_sources():
    """The family's source texts by path."""
    return family_digest.family_sources(_PIPELINES, "hardware_parity*.py", _FAMILY, VALIDATOR)


def _module_source_digest():
    """Immutable source digest of the whole family, used as generator_version."""
    return family_digest.generator_version(_PIPELINES, "hardware_parity*.py", _FAMILY, VALIDATOR)


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


if __package__:
    _expose_package_sibling(__name__)
