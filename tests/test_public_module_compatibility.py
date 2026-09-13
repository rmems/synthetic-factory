#!/usr/bin/env python3
"""Compatibility contracts for CLI modules that re-export split siblings."""

import sys
import unittest
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_rewards  # noqa: E402
import validate_run  # noqa: E402


def star_exports(module):
    """Resolve the namespace Python exposes for ``from module import *``."""

    names = getattr(
        module,
        "__all__",
        [name for name in vars(module) if not name.startswith("_")],
    )
    return {name: getattr(module, name) for name in names}


class PublicModuleCompatibilityTests(unittest.TestCase):
    def test_star_import_preserves_the_pre_split_validator_surface(self):
        namespace = star_exports(validate_run)

        expected = {
            "ALLOWED_PROVENANCE_KIND",
            "ALLOWED_SIM_OR_REAL",
            "HIDDEN_THOUGHT_KEYS",
            "OBSERVABLE_BASIS_RE",
            "REWARD_ARITHMETIC_MARKERS",
            "REWARD_NON_COMPONENT_KEYS",
            "REWARD_TOL",
            "REWARD_UNWEIGHTED_MISMATCH",
            "REWARD_WEIGHTED_MISMATCH",
            "SAFETY_CASE_DECISIONS",
            "SAFETY_CASE_SUCCESS",
            "SAFETY_CASE_TYPES",
            "SAFETY_DECISIONS",
            "THALAMIC_CORE_KEYS",
            "THALAMIC_OBJECT_KEYS",
            "THALAMIC_REQUIRED",
            "THALAMIC_STRING_KEYS",
            "check_episode",
            "check_line",
            "check_meta_round",
            "check_multi_agent",
            "check_provenance",
            "check_provenance_publish",
            "check_reward_total",
            "check_safety_case",
            "check_spike_order",
            "check_spike_stream",
            "check_thalamic",
            "declared_clock_domains",
            "event_time",
            "is_number",
            "main",
            "parse_args",
            "reject_json_constant",
            "terminal_outcome_agrees",
        }
        self.assertEqual(expected - namespace.keys(), set())

    def test_reward_star_import_keeps_cli_helpers_and_hides_private_helpers(self):
        namespace = star_exports(curate_rewards)

        expected = {
            "catalog_record_key",
            "census_jsonl",
            "classify_jsonl",
            "convert_jsonl",
            "convert_run",
            "load_units_migration",
            "load_units_migration_bytes",
            "main",
            "parse_args",
            "units_migration_catalog",
        }
        self.assertEqual(expected - namespace.keys(), set())
        self.assertTrue(
            {"_UNSET", "_canonical_bytes", "_classify"}.isdisjoint(namespace)
        )


if __name__ == "__main__":
    unittest.main()
