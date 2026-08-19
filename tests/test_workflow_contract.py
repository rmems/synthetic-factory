#!/usr/bin/env python3
"""Static safety-contract checks for the Workflow DSL script."""

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".claude" / "skills" / "run-synthetic-factory" / "factory-window.workflow.js"


class WorkflowContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text()

    def test_uses_transactional_reserve_publish_and_frontier_verify(self):
        self.assertIn("round_txn.py reserve", self.text)
        self.assertIn("round_txn.py publish", self.text)
        self.assertIn("round_txn.py frontier", self.text)
        self.assertIn("verification.next_round !== round + 1", self.text)
        self.assertIn("records += verification.records", self.text)

    def test_circuit_breaks_instead_of_continuing_after_agent_failure(self):
        failure_block = self.text.split("if (!result)", 1)[1].split("if (result.factory", 1)[0]
        self.assertIn("break", failure_block)
        self.assertNotIn("continue", failure_block)

    def test_start_round_must_be_positive_integer(self):
        self.assertIn("!Number.isInteger(start) || start < 1", self.text)

    def test_preference_session_a_uses_indexed_staging_names(self):
        session_a = self.text.split("You are Session A", 1)[1].split("You are Session B", 1)[0]
        self.assertNotIn("rejected-0i-", session_a)
        self.assertNotIn("diagnosis-0i-", session_a)
        self.assertIn("rejected-01-r${rr}.json", session_a)
        self.assertIn("rejected-02-r${rr}.json", session_a)
        self.assertIn("rejected-03-r${rr}.json", session_a)
        self.assertIn("diagnosis-01-r${rr}.md", session_a)
        self.assertIn("diagnosis-02-r${rr}.md", session_a)
        self.assertIn("diagnosis-03-r${rr}.md", session_a)

    def test_release_reservation_does_not_treat_mid_publish_as_success(self):
        release = self.text.split("async function releaseReservation", 1)[1]
        release = release.split("const perFactory", 1)[0]
        self.assertIn("receipt.aborted", release)
        self.assertIn("round_txn.py publish", release)
        self.assertIn("resumed mid-publish", release)
        self.assertNotIn("gone/committed/mid-publish", release)
        self.assertNotIn("already committed or mid-publish", release)


if __name__ == "__main__":
    unittest.main()
