#!/usr/bin/env python3
"""Focused regressions for extracted compose-stage repair boundaries."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


TESTS = Path(__file__).resolve().parent
PIPELINES = TESTS.parent / "pipelines"
for _path in (TESTS, PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import curate_coding  # noqa: E402
import compose_curated_identity  # noqa: E402
import compose_curated_source  # noqa: E402
from compose_contract import ComposeDecision, ComposeError  # noqa: E402
from compose_curated_context import RecordContext, SourceCoordinates  # noqa: E402
from compose_curated_record import compose_record  # noqa: E402
from compose_curated_test_support import (  # noqa: E402
    trajectory,
    trajectory_preference_pair,
)


class PreferenceSideIdentityDeferral(unittest.TestCase):
    def test_one_invalid_side_step_defers_to_the_preferences_lane(self):
        """A repairable side row must not be terminally excluded by identity."""

        source = trajectory_preference_pair()
        source["chosen"]["steps"].append(None)
        original = copy.deepcopy(source)
        context = RecordContext(
            SourceCoordinates(
                "tool-use-preference-factory/batch-r01.jsonl",
                3,
                "3" * 64,
            )
        )

        decision = compose_record(source, context)

        self.assertEqual(decision.action, "retained")
        self.assertEqual(source, original)
        self.assertEqual(len(decision.record["chosen"]["steps"]), 2)
        self.assertTrue(decision.record["chosen"]["id"].startswith("sfcur-"))
        self.assertEqual(
            decision.record["chosen"]["provenance"]["kind"], "designed"
        )
        identity_stage = next(
            item for item in decision.stages if item["lane"] == "identity"
        )
        self.assertTrue(
            identity_stage["detail"][
                "preference_steps_deferred_to_preferences_lane"
            ]
        )
        preference_stage = next(
            item for item in decision.stages if item["lane"] == "preferences"
        )
        self.assertEqual(preference_stage["lane_action"], "repaired")
        self.assertIn(curate_coding.REASON_STEPS_EXCLUDED, decision.reason_codes)

    def test_mixed_family_reason_makes_the_identity_stage_publicly_excluded(self):
        """Public stage action follows the source-family exclusion contract."""

        mixed = trajectory_preference_pair()
        mixed["rejected"] = trajectory(action="reject", domain="mixed")
        retained = SimpleNamespace(
            action="retained",
            record=copy.deepcopy(mixed),
            mapping={"reason_codes": ["identity.assigned"], "record_kind": "preference"},
        )
        stages = []

        with mock.patch.object(
            compose_curated_identity.curate_identity,
            "curate_record",
            return_value=retained,
        ):
            outcome = compose_curated_identity._compose_identity_stage_with_source(
                mixed,
                stages,
                SourceCoordinates(
                    "tool-use-preference-factory/batch-r01.jsonl",
                    4,
                    "4" * 64,
                ),
            )

        self.assertIsInstance(outcome, ComposeDecision)
        self.assertEqual(outcome.action, "excluded")
        self.assertEqual(stages[0]["action"], "excluded")
        self.assertEqual(stages[0]["lane_action"], "retained")


class SourceCollaboratorValidation(unittest.TestCase):
    def test_noncallable_deduplicator_is_rejected_instead_of_defaulted(self):
        retained = ComposeDecision(
            "retained",
            {"id": "sfcur-example"},
            (),
            (),
            None,
            "sfcur-example",
        )
        context = compose_curated_source.SourceLineContext(
            "factory/batch-r01.jsonl",
            1,
            "1" * 64,
            record_composer=lambda _record, _context: retained,
            deduplicate_curated_record=object(),
        )

        with self.assertRaisesRegex(
            ComposeError,
            "deduplicator must be callable or None",
        ):
            compose_curated_source.compose_source_line(b'{"id":"source"}', context)


if __name__ == "__main__":
    unittest.main()
