"""Fail-closed refusals of the bounded diagnosis document contract.

The diagnosis bridge is the only channel from Session A to Session B, so
every malformed shape below is refused with a ``PreferenceArmsError`` whose
message names the broken rule. These tests pin those messages.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import MappingProxyType

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import preference_arms_diagnosis as pad

LABEL = "diagnosis-01-r11.md"
_NARRATIVE = "The gate skipped the required check."
_CONTEXT = MappingProxyType({"state": {"case": 1}, "proposed_action": {"action": "hold"}})
_TARGET = MappingProxyType({"per_component": {"safety": 0.5, "task_progress": 0.25}, "total": 0.75})


def _fenced(value) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=dict)
    return f"```json\n{text}\n```"


def _document(*, context=_CONTEXT, target=_TARGET, root_cause=_NARRATIVE) -> bytes:
    sections = (
        ("Shared context", _fenced(context) if context is not None else ""),
        ("Root cause", root_cause),
        ("Cascade effects", _NARRATIVE),
        ("Supervisor catch", _NARRATIVE),
        ("Repair sketch", _NARRATIVE),
        ("Target reward delta", _fenced(target)),
    )
    body = "".join(f"## {name}\n\n{text}\n\n" for name, text in sections)
    return f"# Diagnosis\n\n{body}".encode()


class DiagnosisRefusalCaseMixin:
    def assertRefused(self, payload: bytes, message: str) -> None:
        with self.assertRaises(pad.PreferenceArmsError) as caught:
            pad.validate_diagnosis_document(payload, label=LABEL)
        self.assertIn(message, str(caught.exception))

    def assertRefusedTable(self, cases) -> None:
        for name, payload, message in cases:
            with self.subTest(case=name):
                self.assertRefused(payload, message)


class ArtifactNamingRefusals(unittest.TestCase):
    BAD_NUMBERS = (0, -1, True, 1.0, "1")

    def test_filename_builders_refuse_non_positive_integers(self):
        builders = (
            ("diagnosis round", lambda bad: pad.diagnosis_filenames(bad, 1)),
            ("diagnosis count", lambda bad: pad.diagnosis_filenames(1, bad)),
            ("diagnosis receipt round", pad.diagnosis_receipt_filename),
            ("rejected scratch round", lambda bad: pad.rejected_scratch_filenames(bad, 1)),
            ("rejected scratch count", lambda bad: pad.rejected_scratch_filenames(1, bad)),
        )
        for message, build in builders:
            for bad in self.BAD_NUMBERS:
                with self.subTest(message=message, bad=bad), self.assertRaisesRegex(
                    pad.PreferenceArmsError, message
                ):
                    build(bad)

    def test_valid_numbers_yield_canonical_names(self):
        self.assertEqual(pad.rejected_scratch_filenames(3, 2),
                         ("rejected-01-r03.json", "rejected-02-r03.json"))
        self.assertEqual(pad.diagnosis_receipt_filename(7), "diagnosis-handoff-receipt-r07.json")


class EncodingRefusals(DiagnosisRefusalCaseMixin, unittest.TestCase):
    def test_baseline_document_is_accepted(self):
        result = pad.validate_diagnosis_document(_document(), label=LABEL)
        self.assertEqual(result["target_reward_delta"], _TARGET)

    def test_byte_level_violations_are_refused(self):
        self.assertRefusedTable((
            ("oversized", b"#" * (pad.MAX_DIAGNOSIS_BYTES + 1), "-byte diagnosis limit"),
            ("bare-cr", _document(root_cause="one\rtwo"), "bare carriage return"),
            ("control", _document(root_cause="bell\x07"), "control character"),
        ))


class SharedContextRefusals(DiagnosisRefusalCaseMixin, unittest.TestCase):
    def test_fence_shape_violations_are_refused(self):
        self.assertRefusedTable((
            ("missing-fence", _document(context=None), "exactly one fenced JSON object"),
            ("non-object", _document(context=[1, 2]), "must be a JSON object"),
        ))

    def test_wrong_fence_language_is_refused(self):
        payload = _document().replace(b"```json\n{\"state\"", b"```text\n{\"state\"", 1)
        self.assertRefused(payload, "exactly one fenced JSON object")

    def test_non_object_context_values_are_refused(self):
        context = {"state": [], "proposed_action": {}}
        self.assertRefused(_document(context=context), "values must be JSON objects")

    def test_encoded_marker_strings_are_refused(self):
        for marker in ("data:text/plain", "x%7By", "x%7Dy"):
            with self.subTest(marker=marker):
                context = {"state": {"note": [marker]}, "proposed_action": {}}
                self.assertRefused(_document(context=context), "encoded or serialized payload")

    def test_node_budget_is_enforced(self):
        context = {"state": {"items": [0] * pad.MAX_DIAGNOSIS_NODES}, "proposed_action": {}}
        self.assertRefused(_document(context=context), "shared-context node limit")

    def test_nested_lists_within_budget_are_accepted(self):
        context = {"state": {"items": [[1, "ok"], []]}, "proposed_action": {}}
        result = pad.validate_diagnosis_document(_document(context=context), label=LABEL)
        self.assertEqual(result["shared_context"], context)


class NarrativeRefusals(DiagnosisRefusalCaseMixin, unittest.TestCase):
    def test_bounded_prose_violations_are_refused(self):
        oversized_line = "a" * (pad.MAX_DIAGNOSIS_LINE_CHARS + 1)
        self.assertRefusedTable((
            ("empty", _document(root_cause=""), "'Root cause' is empty"),
            ("long-line", _document(root_cause=oversized_line), "has an oversized line"),
            ("table", _document(root_cause="| a | b |"), "contains a Markdown table"),
        ))


def _target(components, total):
    return _document(target={"per_component": components, "total": total})


class TargetRewardDeltaRefusals(DiagnosisRefusalCaseMixin, unittest.TestCase):
    def test_shape_and_component_count_are_enforced(self):
        many = {f"c{i}": 0.01 for i in range(pad.MAX_DIAGNOSIS_COMPONENTS + 1)}
        self.assertRefusedTable((
            ("extra-key", _document(target={**_TARGET, "note": 1}), "per_component and total"),
            ("list-components", _target([1], 1), "per_component and total"),
            ("empty", _target({}, 1), "must have 1-64 components"),
            ("too-many", _target(many, 0.65), "must have 1-64 components"),
        ))

    def test_component_keys_and_values_are_enforced(self):
        self.assertRefusedTable((
            ("bad-slug", _target({"Safety": 1}, 1), "component 'Safety' must be a finite"),
            ("bool", _target({"safety": True}, 1), "component 'safety' must be a finite"),
            ("string", _target({"safety": "1"}, 1), "component 'safety' must be a finite"),
        ))

    def test_total_is_enforced(self):
        self.assertRefusedTable((
            ("bool-total", _target({"safety": 1}, True), "total must be a finite number"),
            ("non-positive", _target({"safety": -1}, -1), "total must be positive"),
            ("overflow", _target({"a": 10**400}, 1), "exceed the supported numeric range"),
        ))

    def test_integer_components_reconcile_with_the_total(self):
        result = pad.validate_diagnosis_document(_target({"safety": 2, "task": 1}, 3), label=LABEL)
        self.assertEqual(result["target_reward_delta"]["total"], 3)


if __name__ == "__main__":
    unittest.main()
