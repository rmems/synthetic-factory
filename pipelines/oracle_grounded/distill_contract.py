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
``distill_measurements`` (the measurement checks), ``distill_energy_claims`` (the
no-theoretical-energy rule and its structural scan), ``distill_blocks`` (the per-block envelope checks, the generator/oracle
separation rule, ``check_envelope`` and ``check_digest``), ``distill_curation``
(the validator-owned stamp and the fail-closed curation gate),
``distill_jsonl`` (the JSONL I/O), ``distill_labels`` (the family-owned
oracle-label policies and the family leak check, distinct from the structural
checks), ``rng`` (the shared seeded draw stream) and ``refusals`` (the coded
refusal base every family subclasses) -- and every name is re-exported here so
``distill_contract.X`` remains the one entry point the family generators, the
validator and the tests use. The envelope's primitives are bound under their
own names too, so a ``ContractError`` raised by a family generator is caught
through either module.

Standard library only, like the rest of ``pipelines/``.

Supported import forms
----------------------

Two forms are supported, and both may be used in one process in either
order. Every sibling resolves to one module object under both names, so a
``ContractError`` raised through one name is caught through the other:

* the CLI form, with ``pipelines/`` on ``sys.path``:
  ``from oracle_grounded import distill_contract``;
* the package form, with the repository root on ``sys.path``:
  ``from pipelines.oracle_grounded import distill_contract`` or
  ``import pipelines.oracle_grounded.distill_contract``.

``import_twins.bind_import_twin`` binds each sibling, and its package, under
the other name as it finishes importing; ``tests/test_distill_contract.py``
exercises every form and order in a fresh interpreter.
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
from .distill_labels import (
    LABEL_IN_GENERATOR_NAMESPACE,
    POLICY_MISMATCH,
    POLICY_MISSING,
    OracleLabelPolicy,
    check_oracle_label_leak,
    declare_oracle_labels,
    declared_families,
    oracle_label_policy,
)
from .distill_energy_claims import check_no_theoretical_energy_claim
from .distill_measurements import check_measurements, walk_keys
from .distill_vocabulary import (
    AUTHORITY_AUTHORITATIVE,
    AUTHORITY_REFERENCE_ONLY,
    ENERGY_QUANTITIES,
    RESERVED_KEY_SCAN_DEPTH_EXCEEDED,
    ENERGY_TOKENS,
    ENERGY_UNITS,
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
from .refusals import CodedRefusal, code_of, shown
from .refusals import helpers as refusal_helpers
from .rng import MAX_SEED, DrawStream, check_seed

__all__ = (
    "AUTHORITY_AUTHORITATIVE",
    "AUTHORITY_REFERENCE_ONLY",
    "CodedRefusal",
    "ContractError",
    "DrawStream",
    "ENERGY_QUANTITIES",
    "ENERGY_TOKENS",
    "ENERGY_UNITS",
    "FAMILIES",
    "GENERATOR_AUTHORITY",
    "GENERATOR_KINDS",
    "GENERATOR_SECTIONS",
    "GeneratorIdentity",
    "ISO_8601_RE",
    "LABEL_IN_GENERATOR_NAMESPACE",
    "MAX_SEED",
    "MEASURED_ENERGY_METERS",
    "MODELED_METERS",
    "MeasurementOptions",
    "NON_NEGATIVE_QUANTITIES",
    "ORACLE_AUTHORITIES",
    "ORACLE_ONLY_KEYS",
    "ORACLE_TYPES",
    "OracleIdentity",
    "OracleLabelPolicy",
    "OracleRun",
    "OracleUnavailable",
    "POLICY_MISMATCH",
    "POLICY_MISSING",
    "RESERVED_KEY_SCAN_DEPTH_EXCEEDED",
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
    "check_seed",
    "code_of",
    "check_envelope",
    "check_generator_oracle_separation",
    "check_measurements",
    "check_no_theoretical_energy_claim",
    "check_oracle_label_leak",
    "curation_eligible",
    "declare_oracle_labels",
    "declared_families",
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
    "oracle_label_policy",
    "read_jsonl",
    "record_digest",
    "refusal_helpers",
    "shown",
    "stamp_is_bound_to_content",
    "stamp_validation",
    "unvalidated",
    "utc_now_iso",
    "walk_keys",
    "write_jsonl",
)

bind_import_twin(__name__)
