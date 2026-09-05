"""Tests for pipelines/oracle_grounded/parity_contract.py -- the facade.

The contract's rules are tested beside the sibling that owns them
(``test_parity_envelope``, ``test_parity_blocks``, ``test_parity_views``,
``test_parity_view_sets``, ``test_parity_destination``). This module pins the
facade itself: every historical ``contract.<name>`` still resolves, and to the
sibling's own object rather than a copy.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parity_contract_support import contract  # noqa: E402

from oracle_grounded import (  # noqa: E402
    envelope,
    parity_blocks,
    parity_destination,
    parity_envelope,
    parity_terms,
    parity_view_sets,
    parity_views,
)

HISTORICAL_PRIVATE_NAMES = (
    "_is_enum_value",
    "_is_object",
    "_nonempty_str",
    "_is_positive_round",
    "_points_under_raw_tree",
    "_check_generator_produced",
    "_oracle_only_intruders",
    "_derived_membership_errors",
    "_check_derived_digests",
    "_check_claimed_not_real",
    "_check_envelope_identity",
    "_check_envelope_scenario",
    "_check_envelope_meta",
    "_hardware_parity_execution_targets",
    "_is_runtime_status_entry",
    "_nir_equivalence_execution_targets",
    "_record_execution_targets",
    "_check_view_identity",
    "_side_reason_code_errors",
    "_check_view_reason_codes",
    "_check_view_provenance",
    "_view_id_validity_errors",
    "_dropped_record_errors",
    "_orphan_view_errors",
    "_duplicate_view_errors",
    "_view_id_mapping_errors",
    "_scenario_ids_by_round",
    "_round_coverage_error",
)


class FacadeSurface(unittest.TestCase):
    def test_every_public_name_resolves(self):
        for name in contract.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(contract, name))

    def test_historical_private_names_still_resolve(self):
        for name in HISTORICAL_PRIVATE_NAMES:
            with self.subTest(name=name):
                self.assertTrue(callable(getattr(contract, name)))

    def test_public_names_are_the_owning_siblings_objects(self):
        owners = {
            "check_envelope": parity_envelope,
            "check_generator": parity_blocks,
            "check_reason_codes": parity_blocks,
            "raw_tree_destination_error": parity_destination,
            "REASON_CODES": parity_terms,
            "build_training_view": parity_views,
            "training_view_errors": parity_views,
            "view_set_errors": parity_view_sets,
            "catalog_batch_errors": parity_view_sets,
            "strict_json_equal": envelope,
            "PROVENANCE_KINDS": envelope,
        }
        for name, owner in owners.items():
            with self.subTest(name=name):
                self.assertIs(getattr(contract, name), getattr(owner, name))


if __name__ == "__main__":
    unittest.main()
