"""Fail-closed branches of explicit oracle training selection."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_oracle_selection as selection
from compose_contract import ComposeDecision, ComposeError

INVALID_DECLARATION = "COMPOSE.json: invalid oracle selection declaration"
ELIGIBLE = "eligible-training"


def _decision(detail, record=None) -> ComposeDecision:
    stages = ({"lane": "identity", "detail": detail}, {"lane": "rewards"})
    return ComposeDecision(
        "retained", {"id": "r"} if record is None else record, (), stages, {"s": 1}, "r"
    )


def _authority(eligible, reasons) -> dict:
    return {
        "procedural_authority": {
            "eligible_training_candidate": eligible,
            "ineligibility_reasons": reasons,
        }
    }


class SelectionCase(unittest.TestCase):
    def assert_refused(self, message: str, call, *args) -> None:
        with self.assertRaises(ComposeError) as caught:
            call(*args)

        self.assertEqual(str(caught.exception), message)


class ModeTests(SelectionCase):
    def test_non_string_mode_is_refused(self):
        self.assert_refused(
            "oracle selection must be all or eligible-training", selection.require_mode, 1
        )

    def test_unknown_mode_is_refused(self):
        self.assert_refused(
            "oracle selection must be all or eligible-training", selection.descriptor, "some"
        )

    def test_descriptor_names_the_transform(self):
        self.assertEqual(
            selection.descriptor(ELIGIBLE),
            {"name": "oracle-training-selection", "version": 1, "mode": ELIGIBLE},
        )


class PublishedModeTests(SelectionCase):
    def test_absent_declaration_means_all(self):
        self.assertEqual(selection.published_mode({}), "all")

    def test_foreign_declaration_is_refused(self):
        summary = {"oracle_selection": selection.descriptor("all")}

        self.assert_refused(INVALID_DECLARATION, selection.published_mode, summary)

    def test_boolean_version_is_refused(self):
        summary = {"oracle_selection": {"name": selection.NAME, "version": True, "mode": ELIGIBLE}}

        self.assert_refused(INVALID_DECLARATION, selection.published_mode, summary)

    def test_float_version_is_refused(self):
        summary = {"oracle_selection": {"name": selection.NAME, "version": 1.0, "mode": ELIGIBLE}}

        self.assert_refused(INVALID_DECLARATION, selection.published_mode, summary)

    def test_exact_declaration_is_eligible_training(self):
        summary = {"oracle_selection": selection.descriptor(ELIGIBLE)}

        self.assertEqual(selection.published_mode(summary), ELIGIBLE)


class AuthenticatedSourceTests(SelectionCase):
    def test_all_mode_needs_no_oracle_authority(self):
        self.assertIsNone(selection.require_authenticated_source("all", ("a.jsonl",), {}))

    def test_unauthenticated_run_is_refused(self):
        self.assert_refused(
            "oracle training selection requires a complete authenticated oracle run",
            selection.require_authenticated_source,
            ELIGIBLE,
            ("a.jsonl",),
            {},
        )

    def test_partial_authentication_is_refused(self):
        self.assert_refused(
            "oracle training selection does not cover every source member",
            selection.require_authenticated_source,
            ELIGIBLE,
            ("a.jsonl", "b.jsonl"),
            {"a.jsonl": "a.jsonl"},
        )

    def test_complete_authentication_is_accepted(self):
        self.assertIsNone(
            selection.require_authenticated_source(ELIGIBLE, ("a.jsonl",), {"a.jsonl": "x"})
        )


class ApplySelectionTests(SelectionCase):
    def test_all_mode_returns_the_decision_unchanged(self):
        decision = _decision({})

        self.assertIs(selection.apply_selection(decision, "all"), decision)

    def test_unknown_mode_is_refused(self):
        self.assert_refused(
            "oracle selection must be all or eligible-training",
            selection.apply_selection,
            _decision({}),
            "every",
        )

    def test_excluded_record_cannot_be_selected(self):
        decision = ComposeDecision("excluded", None, ("x",), (), None, None)

        self.assert_refused(
            "oracle selection requires a valid retained source record",
            selection.apply_selection,
            decision,
            ELIGIBLE,
        )

    def test_missing_fresh_admission_is_refused(self):
        self.assert_refused(
            "oracle selection requires freshly validated identity admission",
            selection.apply_selection,
            _decision({}),
            ELIGIBLE,
        )

    def test_missing_admission_reasons_are_refused(self):
        self.assert_refused(
            "oracle selection requires fresh admission reasons",
            selection.apply_selection,
            _decision(_authority(True, "none")),
            ELIGIBLE,
        )

    def test_eligible_record_gains_a_retained_selection_stage(self):
        selected = selection.apply_selection(_decision(_authority(True, [])), ELIGIBLE)

        self.assertEqual(selected.action, "retained")
        self.assertEqual(selected.stages[-1]["action"], "retained")
        self.assertEqual(selected.stages[-1]["reason_codes"], [])

    def test_ineligible_record_is_excluded_with_the_selection_reason(self):
        selected = selection.apply_selection(_decision(_authority(False, ["why"])), ELIGIBLE)

        self.assertEqual(
            (selected.action, selected.record, selected.reason_codes),
            ("excluded", None, (selection.REASON,)),
        )
        self.assertEqual((selected.output_id, selected.reward_sidecar), (None, None))
        self.assertEqual(selected.stages[-1]["detail"]["ineligibility_reasons"], ["why"])


if __name__ == "__main__":
    unittest.main()
