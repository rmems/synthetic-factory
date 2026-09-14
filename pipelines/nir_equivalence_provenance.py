#!/usr/bin/env python3
"""The generator's own identity: the family source digest and the catalog stamps.

The validator re-derives these from here, so this is what binds a record to the
code that produced it.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_provenance")
    from .oracle_grounded import family_digest  # noqa: E402
    from .nir_equivalence_catalog import _catalog_digest  # noqa: E402
    from .nir_equivalence_terms import (  # noqa: E402
        VALIDATOR,
        CATALOG_AUTHORSHIP,
        GENERATOR_BLOCK,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_provenance"
    )
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from oracle_grounded import family_digest  # noqa: E402
    from nir_equivalence_catalog import _catalog_digest  # noqa: E402
    from nir_equivalence_terms import (  # noqa: E402
        VALIDATOR,
        CATALOG_AUTHORSHIP,
        GENERATOR_BLOCK,
    )

_FAMILY = (
    "nir_equivalence.py",
    "nir_equivalence_base.py",
    "nir_equivalence_catalog.py",
    "nir_equivalence_cli.py",
    "nir_equivalence_compare.py",
    "nir_equivalence_compare_pair.py",
    "nir_equivalence_execute.py",
    "nir_equivalence_graph.py",
    "nir_equivalence_interpreter.py",
    "nir_equivalence_kernels.py",
    "nir_equivalence_provenance.py",
    "nir_equivalence_record.py",
    "nir_equivalence_runtimes.py",
    "nir_equivalence_terms.py",
    "nir_equivalence_validate_envelope.py",
    "nir_equivalence_validate_replay.py",
    "nir_equivalence_validate_result.py",
    "nir_equivalence_validate_runtimes.py",
    "nir_equivalence_validate_stimulus.py",
    "nir_equivalence_views.py",
)


def _family_sources():
    """The family's source texts by path."""
    return family_digest.family_sources(_PIPELINES, "nir_equivalence*.py", _FAMILY, VALIDATOR)


def _module_source_digest():
    """Immutable source digest of the whole family, used as generator_version."""
    return family_digest.generator_version(_PIPELINES, "nir_equivalence*.py", _FAMILY, VALIDATOR)


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
