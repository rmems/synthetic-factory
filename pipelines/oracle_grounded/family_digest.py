#!/usr/bin/env python3
"""The source digest a split generator stamps as its ``generator_version``.

Both parity generators were one module each and are now families of siblings.
A digest over a single file would have kept attesting a facade while the code
that actually builds records moved out from under it -- and because each
validator re-derives through the same function, that would have stayed green
rather than failing. So the digest covers the whole family.

The family is declared by its caller rather than discovered, so adding a
sibling is a deliberate act; the declaration is then cross-checked against the
directory every time the digest is computed, so a sibling can never be added
and silently left out of it.
"""

from __future__ import annotations

from .import_twins import bind_import_twin

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parents[1]
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from neuro_oracle import digest  # noqa: E402


def family_sources(root, glob, family, validator):
    """The family's source texts by path, or raise if the directory disagrees."""

    found = tuple(sorted(path.relative_to(root).as_posix() for path in root.glob(glob)))
    declared = tuple(sorted(family))
    if found != declared:
        raise RuntimeError(
            f"{validator}: the {glob} family on disk is {found}, but the module "
            f"declares {declared}. generator_version must cover every file that "
            "generates, so reconcile the two before running."
        )
    return [
        {"path": f"pipelines/{name}", "text": (root / name).read_text(encoding="utf-8")}
        for name in declared
    ]


# The in-repo oracle every parity record is generated and re-validated with.
# Its behaviour is part of the evidence, so it is part of generator_version:
# two records produced by behaviourally different oracles must not share one.
ORACLE_GLOB = "neuro_oracle*.py"
ORACLE_FAMILY = (
    "neuro_oracle.py",
    "neuro_oracle_adapter.py",
    "neuro_oracle_availability.py",
    "neuro_oracle_capture.py",
    "neuro_oracle_digest.py",
    "neuro_oracle_model.py",
    "neuro_oracle_observation.py",
    "neuro_oracle_q88.py",
    "neuro_oracle_quantize.py",
    "neuro_oracle_reference.py",
    "neuro_oracle_simulate.py",
)

PARITY_GLOB = "oracle_grounded/parity_*.py"
PARITY_FAMILY = (
    "oracle_grounded/parity_blocks.py",
    "oracle_grounded/parity_contract.py",
    "oracle_grounded/parity_destination.py",
    "oracle_grounded/parity_envelope.py",
    "oracle_grounded/parity_history.py",
    "oracle_grounded/parity_jsonl.py",
    "oracle_grounded/parity_publication.py",
    "oracle_grounded/parity_terms.py",
    "oracle_grounded/parity_view_sets.py",
    "oracle_grounded/parity_views.py",
)
SHARED_SOURCES = (
    "__init__.py",
    "exact_json.py",
    "exact_json_encoding.py",
    "oracle_grounded/__init__.py",
    "oracle_grounded/envelope.py",
    "oracle_grounded/family_digest.py",
    "oracle_grounded/import_twins.py",
    "raw_tree_guard.py",
    "tag_jsonutil.py",
    "validate_run_provenance.py",
    "validate_run_spikes.py",
)

SCHEMA_SOURCES = ("schemas/thalamic-trajectory.schema.json",)


def _shared_sources(root):
    """Explicit common foundation closure; adding a parity sibling is fail-closed."""
    paths = family_sources(root, PARITY_GLOB, PARITY_FAMILY, "parity shared source")
    paths.extend(
        {"path": f"pipelines/{name}", "text": (root / name).read_text(encoding="utf-8")}
        for name in SHARED_SOURCES
    )
    paths.extend(
        {"path": name, "text": (root.parent / name).read_text(encoding="utf-8")}
        for name in SCHEMA_SOURCES
    )
    return paths


def module_source_digest(root, glob, family, validator):
    """Immutable digest of the whole family, used as the in-repo generator_version."""

    return digest({"paths": family_sources(root, glob, family, validator)})


def generator_version(root, glob, family, validator):
    """The family digest with the oracle sources it executes folded in."""
    paths = family_sources(root, glob, family, validator)
    paths += family_sources(root, ORACLE_GLOB, ORACLE_FAMILY, validator)
    paths += _shared_sources(root)
    return digest({"paths": paths})


bind_import_twin(__name__)
