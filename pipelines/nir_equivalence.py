#!/usr/bin/env python3
"""`nir-cross-runtime-equivalence` generator, runtimes, and validator.

The question this family answers is whether a neuromorphic graph *means* the
same thing after it crosses a runtime boundary. Successful serialization and
successful parsing are not evidence of that; matching event streams are.

What actually runs here
-----------------------
No upstream NIR runtime is installed in this repository's environment and none
is vendored: ``nir``, ``nirtorch``, ``snntorch``, ``norse``, ``lava`` and
``sinabs`` are all absent, and there is no ``nir-rs`` build. Those runtimes are
therefore declared as adapters that report ``unavailable`` with a reason code,
and a record produced without them says so on its face.

What *is* executed is a pair of in-repo interpreters:

``nir_reference_v1``
    Reset by subtraction, ``Delay`` counted in whole timesteps, cycles broken
    in node insertion order, and ``LI`` supported.

``nir_reference_v1_altorder``
    Reset to zero, ``Delay`` counted as N-1 timesteps, cycles broken in
    reverse-name order, and ``LI`` unsupported.

Every one of those four differences is a documented, real interoperability
hazard between neuromorphic runtimes rather than an invented bug. But the pair
is still two implementations from one repository: a record produced from them
is evidence about *those conventions*, and is not evidence about ``nir-rs`` or
any upstream backend. The ``runtime_class`` field on every runtime entry says
which kind of evidence it is.

Mismatches are the product here. Nothing in this module repairs, retries, or
filters a divergence.

Usage:
  python3 pipelines/nir_equivalence.py availability
  python3 pipelines/nir_equivalence.py generate <out_dir> [--round N] [--steps N]
  python3 pipelines/nir_equivalence.py validate <path>
  python3 pipelines/nir_equivalence.py training-view <path>
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence")
    from .neuro_oracle import canonical_json, digest  # noqa: E402,F401
    from .nir_equivalence_terms import (  # noqa: E402,F401
        FACTORY_SLUG,
        NUMERIC_TOL,
        ORACLE_PAIRING,
        RECORD_KIND,
        RUNTIME_STATUSES,
        SCHEMA_VERSION,
        STATUS_EXECUTED,
        STATUS_UNAVAILABLE,
        STATUS_UNSUPPORTED,
        UNAVAILABLE_REASON_CODES,
        VALIDATOR,
        contract,
    )
    from .nir_equivalence_graph import (  # noqa: E402,F401
        GraphError,
        evaluation_order,
        parse,
        roundtrip,
        serialize,
        structural_digest,
    )
    from .nir_equivalence_runtimes import (  # noqa: E402,F401
        IN_REPO_RUNTIMES,
        REFERENCE_ALT,
        REFERENCE_V1,
        RuntimeUnavailable,
        UPSTREAM_RUNTIMES,
        UnavailableRuntime,
        UnsupportedConstruct,
        _ALL_RUNTIME_BY_NAME,
        _runtime_capability,
        availability_report,
    )
    from .nir_equivalence_catalog import (  # noqa: E402,F401
        GRAPH_SPECS,
        build_scenario,
        build_scenarios,
    )
    from .nir_equivalence_execute import (  # noqa: E402,F401
        execute_runtime,
    )
    from .nir_equivalence_compare import (  # noqa: E402,F401
        _compare_pair,
        _summarize,
        compare_runtimes,
        convention_delta,
        verdict_for,
    )
    from .nir_equivalence_provenance import (  # noqa: E402,F401
        _FAMILY,
        _catalog_provenance_stamps,
        _family_sources,
        _module_source_digest,
    )
    from .nir_equivalence_record import (  # noqa: E402,F401
        _evidence_lineage,
        build_record,
        generate_records,
    )
    from .nir_equivalence_validate_replay import (  # noqa: E402,F401
        _reexecute_in_repo_runtimes,
    )
    from .nir_equivalence_validate_result import (  # noqa: E402,F401
        validate_record,
        validate_records,
    )
    from .nir_equivalence_views import (  # noqa: E402,F401
        build_training_views,
        training_view,
        training_view_errors,
    )
    from .nir_equivalence_cli import (  # noqa: E402,F401
        main,
        parse_args,
        read_jsonl,
        write_jsonl,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence"
    )
    from neuro_oracle import canonical_json, digest  # noqa: E402,F401
    from nir_equivalence_terms import (  # noqa: E402,F401
        FACTORY_SLUG,
        NUMERIC_TOL,
        ORACLE_PAIRING,
        RECORD_KIND,
        RUNTIME_STATUSES,
        SCHEMA_VERSION,
        STATUS_EXECUTED,
        STATUS_UNAVAILABLE,
        STATUS_UNSUPPORTED,
        UNAVAILABLE_REASON_CODES,
        VALIDATOR,
        contract,
    )
    from nir_equivalence_graph import (  # noqa: E402,F401
        GraphError,
        evaluation_order,
        parse,
        roundtrip,
        serialize,
        structural_digest,
    )
    from nir_equivalence_runtimes import (  # noqa: E402,F401
        IN_REPO_RUNTIMES,
        REFERENCE_ALT,
        REFERENCE_V1,
        RuntimeUnavailable,
        UPSTREAM_RUNTIMES,
        UnavailableRuntime,
        UnsupportedConstruct,
        _ALL_RUNTIME_BY_NAME,
        _runtime_capability,
        availability_report,
    )
    from nir_equivalence_catalog import (  # noqa: E402,F401
        GRAPH_SPECS,
        build_scenario,
        build_scenarios,
    )
    from nir_equivalence_execute import (  # noqa: E402,F401
        execute_runtime,
    )
    from nir_equivalence_compare import (  # noqa: E402,F401
        _compare_pair,
        _summarize,
        compare_runtimes,
        convention_delta,
        verdict_for,
    )
    from nir_equivalence_provenance import (  # noqa: E402,F401
        _FAMILY,
        _catalog_provenance_stamps,
        _family_sources,
        _module_source_digest,
    )
    from nir_equivalence_record import (  # noqa: E402,F401
        _evidence_lineage,
        build_record,
        generate_records,
    )
    from nir_equivalence_validate_replay import (  # noqa: E402,F401
        _reexecute_in_repo_runtimes,
    )
    from nir_equivalence_validate_result import (  # noqa: E402,F401
        validate_record,
        validate_records,
    )
    from nir_equivalence_views import (  # noqa: E402,F401
        build_training_views,
        training_view,
        training_view_errors,
    )
    from nir_equivalence_cli import (  # noqa: E402,F401
        main,
        parse_args,
        read_jsonl,
        write_jsonl,
    )

__all__ = [
    "FACTORY_SLUG",
    "GRAPH_SPECS",
    "GraphError",
    "IN_REPO_RUNTIMES",
    "NUMERIC_TOL",
    "ORACLE_PAIRING",
    "RECORD_KIND",
    "REFERENCE_ALT",
    "REFERENCE_V1",
    "RUNTIME_STATUSES",
    "RuntimeUnavailable",
    "SCHEMA_VERSION",
    "STATUS_EXECUTED",
    "STATUS_UNAVAILABLE",
    "STATUS_UNSUPPORTED",
    "UNAVAILABLE_REASON_CODES",
    "UPSTREAM_RUNTIMES",
    "UnavailableRuntime",
    "UnsupportedConstruct",
    "VALIDATOR",
    "availability_report",
    "build_record",
    "build_scenario",
    "build_scenarios",
    "build_training_views",
    "canonical_json",
    "compare_runtimes",
    "contract",
    "convention_delta",
    "digest",
    "evaluation_order",
    "execute_runtime",
    "generate_records",
    "main",
    "parse",
    "parse_args",
    "read_jsonl",
    "roundtrip",
    "serialize",
    "structural_digest",
    "training_view",
    "training_view_errors",
    "validate_record",
    "validate_records",
    "verdict_for",
    "write_jsonl",
]

if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(main())
