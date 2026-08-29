#!/usr/bin/env python3
"""The generating surfaces actually run the gate."""

import unittest

from preference_arms_support import (  # noqa: E402
    REPO,
)
import preference_arms  # noqa: E402


class ProtocolIsDocumentedAndWired(unittest.TestCase):
    """The gate only helps if the generating surfaces actually run it."""

    @classmethod
    def setUpClass(cls):
        cls.doc = (REPO / "docs" / "preference-isolation.md").read_text()
        cls.prompt = (REPO / "prompts" / "05-failure-as-fuel-preference-cascade.md").read_text()
        cls.workflow = (
            REPO / ".claude" / "skills" / "run-synthetic-factory" / "factory-window.workflow.js"
        ).read_text()
        cls.publisher = (REPO / "pipelines" / "round_txn.py").read_text()

    def test_single_session_path_is_deprecated_in_docs_and_prompt(self):
        self.assertIn("single-session path is deprecated", self.doc.lower())
        self.assertIn("single-session path is DEPRECATED", self.prompt)

    def test_docs_and_prompt_name_the_arm_gate_command(self):
        for text in (self.doc, self.prompt):
            self.assertIn("pipelines/preference_arms.py", text)

    def test_protocol_docs_do_not_create_markdown_work_items(self):
        self.assertNotRegex(self.doc, r"(?m)^\s*[-*]\s+\[[ xX]\]")

    def test_session_b_runs_the_arm_gate_before_publishing(self):
        session_b = self.workflow.split("You are Session B", 1)[1]
        gate = session_b.index("preference_arms.py")
        publish = session_b.index("round_txn.py publish")
        self.assertLess(gate, publish)

    def test_round_publisher_is_the_mandatory_gate(self):
        self.assertIn("validate_preference_arm_gate", self.publisher)
        self.assertIn("preference_arm_gate", self.publisher)
        self.assertIn("require_trusted_isolation=True", self.publisher)
        self.assertIn("validate_preference_diagnosis_handoff", self.publisher)
        self.assertIn("preference_diagnosis_handoff", self.publisher)

    def test_workflow_stamps_the_two_session_attestation(self):
        self.assertIn(f'meta.isolation="{preference_arms.TWO_SESSION}"', self.workflow)

    def test_workflow_reservation_carries_the_publisher_marker(self):
        self.assertIn(
            f"--preference-isolation {preference_arms.TWO_SESSION}",
            self.workflow,
        )

    def test_content_blind_controller_reserves_before_session_a(self):
        reservation = self.workflow.index("const reservation = await agent")
        session_a = self.workflow.index("const sessionA = await agent")
        self.assertLess(reservation, session_a)
        self.assertIn(
            "outputs/staging/${args.date}/${expected.factory.slug}/r${expected.rr}-",
            self.workflow,
        )
        self.assertNotIn("outputs/raw/${args.date}/.staging", self.workflow)
        invalid_receipt = self.workflow.split("if (!preferenceReservationIsValid", 1)[1].split(
            "const sessionA", 1
        )[0]
        self.assertIn("releaseReservation(factory, round, rr, null)", invalid_receipt)
        session_a_prompt = self.workflow.split("You are Session A", 1)[1].split(
            "You are Session B", 1
        )[0]
        self.assertNotIn("round_txn.py reserve", session_a_prompt)

    def test_workflow_validates_the_exact_diagnosis_only_handoff(self):
        validation = self.workflow.index("preferenceHandoffIsValid(")
        session_b = self.workflow.index("You are Session B")
        self.assertLess(validation, session_b)
        self.assertIn("preferenceDiagnosisFiles(factory.count, rr)", self.workflow)
        self.assertIn(
            "^diagnosis-[0-9]{2}-r(0[1-9]|[1-9][0-9]+)\\\\.md$",
            self.workflow,
        )

    def test_end_to_end_example_passes_verify_handoff_an_absolute_path(self):
        # `verify_diagnosis_handoff` refuses a relative staging path, so an
        # operator following the example from the repository root has to be
        # given the absolute one `reserve` already returned.
        example = self.doc.split("## 4. End-to-end example", 1)[1]
        verify = example.split("preference_arms.py verify-handoff", 1)[1].split("\n#", 1)[0]
        self.assertNotIn("outputs/staging", verify)
        self.assertIn("$STAGE", verify)

    def test_end_to_end_example_captures_the_returned_staging_dir(self):
        example = self.doc.split("## 4. End-to-end example", 1)[1]
        reserve = example.index("round_txn.py reserve")
        self.assertLess(example.index("STAGE=$("), reserve)
        self.assertIn("staging_dir", example[: example.index("verify-handoff")])

    def test_read_only_verifier_runs_after_session_a_and_before_session_b(self):
        session_a = self.workflow.index("const sessionA = await agent")
        verification = self.workflow.index("const diagnosisVerification = await agent")
        session_b = self.workflow.index("You are Session B")
        self.assertLess(session_a, verification)
        self.assertLess(verification, session_b)
        self.assertIn("preference_arms.py verify-handoff", self.workflow)
        self.assertIn("--write-receipt", self.workflow)
        self.assertIn("preferenceDiagnosisVerificationIsValid(", self.workflow)
        self.assertIn("Number.isSafeInteger(item.bytes)", self.workflow)
        self.assertIn("receipt.reservation_token === reservation.reserve_token", self.workflow)
        self.assertIn("verifiedDiagnosisFiles", self.workflow)

if __name__ == "__main__":
    unittest.main()
