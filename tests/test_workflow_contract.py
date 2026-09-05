#!/usr/bin/env python3
"""Static safety-contract checks for the Workflow DSL script.

The prompt-driven generation lane was retired in #184 (preserved at tag
``legacy-prompt-factory-v0.2``). These checks assert the generator-neutral
contract: the workflow drives ``round_txn.py`` transactions, isolates lane
failures, and carries the token-efficiency NOTES latch without referencing
the retired ``prompts/`` tree.
"""

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".claude" / "skills" / "run-synthetic-factory" / "factory-window.workflow.js"
REGISTRY = REPO / "config" / "FACTORY-REGISTRY.json"
DOCS = REPO / "docs" / "token-efficiency.md"
QODANA_WORKFLOW = REPO / ".github" / "workflows" / "qodana.yml"

sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402


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


class NovelCoverageNotesContract(unittest.TestCase):
    """Every generation lane must ask for the NOTES latch line.

    The token-efficiency early-stop (docs/token-efficiency.md) can only fire
    on rounds whose NOTES report `Novel coverage: <N>%`. The retired prompt
    lane carried that requirement in each factory prompt (preserved at tag
    ``legacy-prompt-factory-v0.2``); on current ``main`` the workflow lane
    briefs carry it, and ``round_txn.py publish`` enforces it on every
    registered lane.
    """

    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text()

    def test_workflow_is_generator_neutral(self):
        self.assertNotIn("prompts/", self.workflow)
        self.assertIn("config/FACTORY-REGISTRY.json", self.workflow)

    def test_workflow_lane_briefs_require_the_notes_line(self):
        self.assertIn("Novel coverage: <N>%", self.workflow)

    def test_the_contract_example_parses_with_the_shipped_regex(self):
        example = "Novel coverage: 12.3%"
        self.assertIn(example, DOCS.read_text())
        match = round_txn.NOVEL_COVERAGE_RE.fullmatch(example)
        self.assertIsNotNone(match)
        self.assertEqual(float(match.group(1)), 12.3)

    def test_strict_publish_and_workflow_parsers_require_one_physical_line(self):
        split_claim = "Novel coverage:\n80% of tests passed.\n"
        self.assertIsNone(round_txn.NOVEL_COVERAGE_RE.search(split_claim))
        self.assertIsNotNone(round_txn.LEGACY_NOVEL_COVERAGE_RE.search(split_claim))
        workflow = WORKFLOW.read_text()
        self.assertIn(r"^[ \t]*novel", workflow)
        self.assertNotIn(r"/^\s*novel", workflow)

    def test_strict_parser_accepts_only_horizontal_whitespace(self):
        self.assertIsNone(round_txn.NOVEL_COVERAGE_RE.fullmatch("\vNovel coverage: 12%"))
        self.assertIsNone(round_txn.NOVEL_COVERAGE_RE.fullmatch("Novel\fcoverage: 12%"))
        self.assertIsNotNone(round_txn.NOVEL_COVERAGE_RE.fullmatch("\tNovel coverage:\t12%\t"))

    def test_strict_parser_accepts_only_ascii_digits(self):
        self.assertIsNone(round_txn.NOVEL_COVERAGE_RE.fullmatch("Novel coverage: ٤%"))
        self.assertIsNone(round_txn.NOVEL_COVERAGE_RE.fullmatch("Novel coverage: １２%"))
        self.assertIsNotNone(round_txn.NOVEL_COVERAGE_RE.fullmatch("Novel coverage: 12.5%"))

    def test_workflow_parser_requires_one_complete_labeled_line(self):
        workflow = WORKFLOW.read_text()
        self.assertIn(r".split(/\r\n|\n|\r/)", workflow)
        self.assertIn(r"%[ \t]*$/i", workflow)
        self.assertIn("labeledLines.length !== 1", workflow)

    def test_docs_and_workflow_agree_on_the_threshold(self):
        docs = DOCS.read_text()
        self.assertIn("Novel coverage: <N>%", docs)
        self.assertIn("5%", docs)
        workflow = WORKFLOW.read_text()
        self.assertIn("docs/token-efficiency.md", workflow)
        self.assertIn("5", workflow)


class RasterGateProducerContract(unittest.TestCase):
    """Every lane the publish gate holds to the raster contract is registered.

    ``round_txn.RASTER_FACTORY_SLUGS`` refuses a staged round whose records
    carry no ``raster`` / ``gate_snn`` sidecar. The retired prompt lane
    documented those sidecars per factory prompt (preserved at tag
    ``legacy-prompt-factory-v0.2``); on current ``main`` the registry is the
    identity authority, so each gated lane must resolve to an exact
    ``path_id`` row. The sidecar shapes themselves are pinned by
    ``schemas/raster.schema.json`` and the ``test_curate_bridge_raster*``
    suites.
    """

    @classmethod
    def setUpClass(cls):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.path_ids = {row["path_id"] for row in registry["factories"]}

    def test_every_gated_lane_is_a_registered_factory(self):
        self.assertTrue(round_txn.RASTER_FACTORY_SLUGS, "raster gate has no lanes")
        missing = sorted(set(round_txn.RASTER_FACTORY_SLUGS) - self.path_ids)
        self.assertEqual(
            missing,
            [],
            f"gated lanes without a registry row: {missing}",
        )


class QodanaWorkflowContract(unittest.TestCase):
    def test_pull_requests_scan_only_changed_files(self):
        text = QODANA_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pr-mode: ${{ github.event_name == 'pull_request' }}", text)
        self.assertNotIn("pr-mode: false", text)

    def test_actions_are_pinned_without_persisted_checkout_credentials(self):
        text = QODANA_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("actions/checkout@11d5960a326750d5838078e36cf38b85af677262", text)
        self.assertIn(
            "JetBrains/qodana-action@4861e015da555e86a72b862892aba6c2b93e6891",
            text,
        )
        self.assertIn("persist-credentials: false", text)


if __name__ == "__main__":
    unittest.main()
