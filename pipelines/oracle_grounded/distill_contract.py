#!/usr/bin/env python3
"""Oracle-grounded record contract for the distillation dataset families.

Introduced by issue #78 for the three control-oriented families:

* ``neuromorphic-fault-recovery``
* ``snn-energy-routing-preferences``
* ``moe-router-distillation-trajectories``

The envelope follows the shared contract sketched in the parent epic (#76):
``generator`` / ``scenario`` / ``intervention`` / ``candidate_prediction`` /
``oracle`` / ``result`` / ``provenance`` / ``validation``.

Three invariants matter more than the field list:

1. **Generators propose, oracles decide.** ``generator.authority`` is pinned to
   ``propose_only``. Any oracle-measured key (``measurements``, ``outcome``,
   ``energy_j``, ``router_logits``, ...) appearing inside a generator-owned
   namespace is a contract violation, not a convenience.
2. **Measurements carry units and a meter.** Energy-class quantities are only
   accepted from a meter that physically measures energy. An analytic
   operation-count or synaptic-operation model can be recorded, but it can
   never stand in for a measured joule.
3. **Nothing self-certifies.** Producers write ``validation.status =
   "unvalidated"``. Only a validator may stamp ``passed``/``failed``, and only
   with its own name and version attached. Curation fails closed unless an
   *authoritative* oracle actually produced a measured result.

This module is the distillation extension of the shared record envelope in
:mod:`oracle_grounded.envelope` (#172). The envelope owns the domain-neutral
primitives -- the section names, ``ContractError`` / ``OracleUnavailable``,
canonical JSON and ``record_digest``, the bounded reserved-key scan and the
NaN/Infinity parse hooks -- and the distillation contract adds only what the
families need. It is split by responsibility across sibling modules --
``distill_vocabulary`` (the families, the schema-version pin, the kind / type /
authority / status vocabularies, the oracle-only key set and the unit / meter /
energy registry), ``distill_builders`` (the block and record builders),
``distill_measurements`` (the measurement checks and the no-theoretical-energy
rule), ``distill_blocks`` (the per-block envelope checks, the generator/oracle
separation rule, ``check_envelope`` and ``check_digest``), ``distill_curation``
(the validator-owned stamp and the fail-closed curation gate) and
``distill_jsonl`` (the JSONL I/O) -- and every name is re-exported here so
``distill_contract.X`` remains the one entry point the family generators, the
validator and the tests use. The envelope's primitives are bound under their
own names too, so a ``ContractError`` raised by a family generator is caught
through either module.

Standard library only, like the rest of ``pipelines/``. Importable both as
``oracle_grounded.distill_contract`` (with ``pipelines/`` on ``sys.path``, the
CLI convention) and as ``pipelines.oracle_grounded.distill_contract`` from the
repository root; each sibling binds both forms to one module object the same
way.
"""

from __future__ import annotations

from .distill_blocks import (
    check_digest,
    check_envelope,
    check_generator_oracle_separation,
)
from .distill_builders import (
    GeneratorIdentity,
    MeasurementOptions,
    OracleIdentity,
    OracleRun,
    Proposal,
    RecordIdentity,
    Verdict,
    build_record,
    new_generator,
    new_measurement,
    new_oracle,
    new_provenance,
    new_result,
    unvalidated,
)
from .distill_curation import (
    curation_eligible,
    stamp_is_bound_to_content,
    stamp_validation,
)
from .distill_jsonl import iter_jsonl, read_jsonl, write_jsonl
from .distill_measurements import (
    ENERGY_KEY_HINTS,
    check_measurements,
    check_no_theoretical_energy_claim,
    walk_keys,
)
from .distill_vocabulary import (
    AUTHORITY_AUTHORITATIVE,
    AUTHORITY_REFERENCE_ONLY,
    ENERGY_QUANTITIES,
    FAMILIES,
    GENERATOR_AUTHORITY,
    GENERATOR_KINDS,
    GENERATOR_SECTIONS,
    ISO_8601_RE,
    MEASURED_ENERGY_METERS,
    MODELED_METERS,
    NON_NEGATIVE_QUANTITIES,
    ORACLE_AUTHORITIES,
    ORACLE_ONLY_KEYS,
    ORACLE_TYPES,
    PREDICTION_FREE_KEYS,
    PREDICTION_PREFIX,
    QUANTITY_UNITS,
    RESULT_ABSTAINED,
    RESULT_MEASURED,
    RESULT_STATUSES,
    SCHEMA_VERSION,
    SHA256_RE,
    UNIT_INTERVAL_QUANTITIES,
    VALIDATION_FAILED,
    VALIDATION_PASSED,
    VALIDATION_STATUSES,
    VALIDATION_UNVALIDATED,
    ContractError,
    OracleUnavailable,
    canonical_json,
    is_enum_value,
    is_genuine_int,
    is_number,
    is_true,
    missing_string,
    record_digest,
    utc_now_iso,
)
from .import_twins import bind_import_twin

__all__ = (
    "AUTHORITY_AUTHORITATIVE",
    "AUTHORITY_REFERENCE_ONLY",
    "ContractError",
    "ENERGY_KEY_HINTS",
    "ENERGY_QUANTITIES",
    "FAMILIES",
    "GENERATOR_AUTHORITY",
    "GENERATOR_KINDS",
    "GENERATOR_SECTIONS",
    "GeneratorIdentity",
    "ISO_8601_RE",
    "MEASURED_ENERGY_METERS",
    "MODELED_METERS",
    "MeasurementOptions",
    "NON_NEGATIVE_QUANTITIES",
    "ORACLE_AUTHORITIES",
    "ORACLE_ONLY_KEYS",
    "ORACLE_TYPES",
    "OracleIdentity",
    "OracleRun",
    "OracleUnavailable",
    "PREDICTION_FREE_KEYS",
    "PREDICTION_PREFIX",
    "Proposal",
    "QUANTITY_UNITS",
    "RESULT_ABSTAINED",
    "RESULT_MEASURED",
    "RESULT_STATUSES",
    "RecordIdentity",
    "SCHEMA_VERSION",
    "SHA256_RE",
    "UNIT_INTERVAL_QUANTITIES",
    "VALIDATION_FAILED",
    "VALIDATION_PASSED",
    "VALIDATION_STATUSES",
    "VALIDATION_UNVALIDATED",
    "Verdict",
    "build_record",
    "canonical_json",
    "check_digest",
    "check_envelope",
    "check_generator_oracle_separation",
    "check_measurements",
    "check_no_theoretical_energy_claim",
    "curation_eligible",
    "is_enum_value",
    "is_genuine_int",
    "is_number",
    "is_true",
    "iter_jsonl",
    "missing_string",
    "new_generator",
    "new_measurement",
    "new_oracle",
    "new_provenance",
    "new_result",
    "read_jsonl",
    "record_digest",
    "stamp_is_bound_to_content",
    "stamp_validation",
    "unvalidated",
    "utc_now_iso",
    "walk_keys",
    "write_jsonl",
)

bind_import_twin(__name__)
