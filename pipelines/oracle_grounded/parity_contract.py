#!/usr/bin/env python3
"""Shared record contract for oracle-grounded parity datasets.

Both parity families (`hardware-parity-spike-trajectories` and
`nir-cross-runtime-equivalence`) emit records with the same envelope so that
one set of rules can enforce the epic's governing constraint:

    generators propose experiments; oracles produce truth

Concretely this module enforces four things that the family validators build
on top of:

* generator output and oracle output live in separate, differently-named
  fields, and the generator block must declare that it cannot certify a
  result (``may_certify_oracle_result: false``);
* a ``candidate_prediction`` may never carry the keys an oracle would fill,
  so generator-written scenario text cannot be mistaken for a measurement;
* ``result`` must be marked oracle-backed and name the oracle output digests
  it was derived from, and it must carry a verdict from a fixed vocabulary;
* a training view derived from a record cannot drop, soften, or relabel a
  parity failure.

The domain-neutral primitives come from the shared ``oracle_grounded.envelope``
foundation (#172): the repository-wide ``provenance.kind`` vocabulary
(``PROVENANCE_KINDS``), the NaN/Infinity parse hooks (``reject_json_constant``,
``reject_nonfinite_float``) and type-strict JSON equality
(``strict_json_equal``) are bound from there and never redefined here. This
module owns what the parity families decide for themselves: the record kinds
and their dataset/schema pins, the verdict and reason-code vocabularies, the
oracle-only keys, the envelope key list and ``check_envelope``, the immutable
``outputs/raw`` guard, and the training-view rules.

Stdlib only. No JSON Schema library is available in this repository, so the
``schemas/*.schema.json`` files are documentation and these functions are the
enforcement. Importable as ``oracle_grounded.parity_contract`` with
``pipelines/`` on ``sys.path`` (the CLI convention) and as
``pipelines.oracle_grounded.parity_contract`` from the repository root.

This module is the stable facade. The implementation lives in sibling modules
split by responsibility, re-exported here so every ``contract.<name>`` reader
keeps one surface:

* ``parity_terms`` -- the kinds, pins, verdicts, reason codes, oracle-only
  keys, envelope keys and shape predicates;
* ``parity_destination`` -- the immutable ``outputs/raw`` guard;
* ``parity_blocks`` -- the per-block rules (reason codes, generator,
  candidate prediction, result, provenance, validation);
* ``parity_envelope`` -- ``check_envelope`` and its identity/scenario/meta
  rules;
* ``parity_views`` -- the training-view builder and gate;
* ``parity_view_sets`` -- view-set and catalog-batch authentication.
"""


from __future__ import annotations

from . import envelope as _envelope
from . import parity_blocks as _blocks
from . import parity_destination as _destination
from . import parity_envelope as _record_envelope
from . import parity_terms as _terms
from . import parity_view_sets as _view_sets
from . import parity_views as _views

# Shared foundation (``oracle_grounded.envelope``), bound explicitly so the
# family readers and tests keep reaching them as ``contract.<name>`` without
# asking static analyzers to treat unused imports as use.
#
# ``PROVENANCE_KINDS`` is the repository-wide ``provenance.kind`` vocabulary
# (schemas/provenance.md) as the validator reads it from the thalamic schema.
# A genuine FPGA run is `hil`; a reference-model run is `simulated`. `real` is
# never emitted here, as everywhere else in the factory.
PROVENANCE_KINDS = _envelope.PROVENANCE_KINDS
reject_json_constant = _envelope.reject_json_constant
reject_nonfinite_float = _envelope.reject_nonfinite_float
strict_json_equal = _envelope.strict_json_equal
_is_enum_value = _envelope.is_enum_value

# Vocabularies and shape predicates (``parity_terms``).
CONTRACT_VERSION = _terms.CONTRACT_VERSION
KIND_HARDWARE_PARITY = _terms.KIND_HARDWARE_PARITY
KIND_NIR_EQUIVALENCE = _terms.KIND_NIR_EQUIVALENCE
RECORD_KINDS = _terms.RECORD_KINDS
DATASET_FOR_KIND = _terms.DATASET_FOR_KIND
SCHEMA_VERSION_FOR_KIND = _terms.SCHEMA_VERSION_FOR_KIND
VERDICT_MATCH = _terms.VERDICT_MATCH
VERDICT_MISMATCH = _terms.VERDICT_MISMATCH
VERDICT_UNSUPPORTED = _terms.VERDICT_UNSUPPORTED
VERDICT_INCONCLUSIVE = _terms.VERDICT_INCONCLUSIVE
VERDICTS = _terms.VERDICTS
PASSING_VERDICTS = _terms.PASSING_VERDICTS
ORACLE_ONLY_KEYS = _terms.ORACLE_ONLY_KEYS
REASON_CODES = _terms.REASON_CODES
ENVELOPE_KEYS = _terms.ENVELOPE_KEYS
_is_object = _terms._is_object
_nonempty_str = _terms._nonempty_str
_is_positive_round = _terms._is_positive_round

# The immutable ``outputs/raw`` guard (``parity_destination``).
raw_tree_destination_error = _destination.raw_tree_destination_error
_points_under_raw_tree = _destination._points_under_raw_tree

# Per-block rules (``parity_blocks``).
check_reason_codes = _blocks.check_reason_codes
check_generator = _blocks.check_generator
check_candidate_prediction = _blocks.check_candidate_prediction
check_result = _blocks.check_result
check_provenance = _blocks.check_provenance
check_validation_block = _blocks.check_validation_block
_check_generator_produced = _blocks._check_generator_produced
_oracle_only_intruders = _blocks._oracle_only_intruders
_derived_membership_errors = _blocks._derived_membership_errors
_check_derived_digests = _blocks._check_derived_digests
_check_claimed_not_real = _blocks._check_claimed_not_real

# The shared envelope (``parity_envelope``).
check_envelope = _record_envelope.check_envelope
_check_envelope_identity = _record_envelope._check_envelope_identity
_check_envelope_scenario = _record_envelope._check_envelope_scenario
_check_envelope_meta = _record_envelope._check_envelope_meta

# Training views (``parity_views``).
TRAINING_VIEW_KEYS = _views.TRAINING_VIEW_KEYS
ORACLE_INCOMPLETE_REASON_CODES = _views.ORACLE_INCOMPLETE_REASON_CODES
oracle_is_complete = _views.oracle_is_complete
build_training_view = _views.build_training_view
training_view_errors = _views.training_view_errors
_hardware_parity_execution_targets = _views._hardware_parity_execution_targets
_is_runtime_status_entry = _views._is_runtime_status_entry
_nir_equivalence_execution_targets = _views._nir_equivalence_execution_targets
_record_execution_targets = _views._record_execution_targets
_check_view_identity = _views._check_view_identity
_side_reason_code_errors = _views._side_reason_code_errors
_check_view_reason_codes = _views._check_view_reason_codes
_check_view_provenance = _views._check_view_provenance

# View-set and catalog-batch authentication (``parity_view_sets``).
view_set_errors = _view_sets.view_set_errors
catalog_batch_errors = _view_sets.catalog_batch_errors
_view_id_validity_errors = _view_sets._view_id_validity_errors
_dropped_record_errors = _view_sets._dropped_record_errors
_orphan_view_errors = _view_sets._orphan_view_errors
_duplicate_view_errors = _view_sets._duplicate_view_errors
_view_id_mapping_errors = _view_sets._view_id_mapping_errors
_scenario_ids_by_round = _view_sets._scenario_ids_by_round
_round_coverage_error = _view_sets._round_coverage_error

__all__ = [
    "CONTRACT_VERSION",
    "DATASET_FOR_KIND",
    "ENVELOPE_KEYS",
    "KIND_HARDWARE_PARITY",
    "KIND_NIR_EQUIVALENCE",
    "ORACLE_INCOMPLETE_REASON_CODES",
    "ORACLE_ONLY_KEYS",
    "PASSING_VERDICTS",
    "PROVENANCE_KINDS",
    "REASON_CODES",
    "RECORD_KINDS",
    "SCHEMA_VERSION_FOR_KIND",
    "TRAINING_VIEW_KEYS",
    "VERDICTS",
    "VERDICT_INCONCLUSIVE",
    "VERDICT_MATCH",
    "VERDICT_MISMATCH",
    "VERDICT_UNSUPPORTED",
    "build_training_view",
    "catalog_batch_errors",
    "check_candidate_prediction",
    "check_envelope",
    "check_generator",
    "check_provenance",
    "check_reason_codes",
    "check_result",
    "check_validation_block",
    "oracle_is_complete",
    "raw_tree_destination_error",
    "reject_json_constant",
    "reject_nonfinite_float",
    "strict_json_equal",
    "training_view_errors",
    "view_set_errors",
]
