"""Complete-catalog and reservation checks after deep parity record validation."""

from __future__ import annotations

from .import_twins import bind_import_twin
from .parity_jsonl import read_jsonl
from .parity_view_sets import catalog_batch_errors


def _catalog_ids(kind):
    if __name__.startswith("pipelines."):
        from ..hardware_parity_catalog import SCENARIO_SPECS
        from ..nir_equivalence_catalog import _GRAPH_CATALOG_BY_ID
    else:
        from hardware_parity_catalog import SCENARIO_SPECS
        from nir_equivalence_catalog import _GRAPH_CATALOG_BY_ID
    return {
        "hardware_parity": tuple(spec["id"] for spec in SCENARIO_SPECS),
        "nir_equivalence": tuple(_GRAPH_CATALOG_BY_ID),
    }[kind]


def batch_errors(path, kind, reserved_round):
    """Require all scenarios exactly once at the independently reserved round.

    The transaction calls this only after deep per-record validation. Parsing
    the captured bytes here also rejects ambiguous duplicate JSON fields.
    """
    records, errors = read_jsonl(path)
    if errors:
        return errors
    errors = catalog_batch_errors(records, _catalog_ids(kind), str(path))
    if any(record["meta"]["round"] != reserved_round for record in records):
        errors.append(f"{path}: parity records must match reserved round {reserved_round}")
    return errors


bind_import_twin(__name__)
