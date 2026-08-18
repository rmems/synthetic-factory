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


if __name__ == "__main__":
    unittest.main()
