#!/usr/bin/env python3
"""Static safety-contract checks for the Workflow DSL script and prompts."""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".claude" / "skills" / "run-synthetic-factory" / "factory-window.workflow.js"
PROMPTS = REPO / "prompts"
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
    """Every round-transactional prompt must ask for the NOTES latch line.

    The token-efficiency early-stop (docs/token-efficiency.md) can only fire
    on rounds whose NOTES report `Novel coverage: <N>%`.  A prompt that drives
    round_txn publish but never asks for the line produces rounds the latch
    cannot read, which is exactly how the 2026-08-19 harvest ended up with
    0/49 parseable NOTES.
    """

    @classmethod
    def setUpClass(cls):
        cls.prompts = {path.name: path.read_text() for path in sorted(PROMPTS.glob("*.md"))}
        cls.transactional = {
            name: text for name, text in cls.prompts.items() if "round_txn.py" in text
        }

    def test_every_transactional_prompt_requires_the_notes_line(self):
        self.assertTrue(self.transactional, "no transactional prompts found")
        missing = sorted(
            name for name, text in self.transactional.items() if "Novel coverage: <N>%" not in text
        )
        self.assertEqual(missing, [], f"prompts missing the NOTES contract: {missing}")

    def test_both_shared_contracts_carry_the_line(self):
        for name in ("_factory-contract.md", "_agentic-factory-contract.md"):
            self.assertIn("Novel coverage: <N>%", self.transactional[name], name)

    def test_legacy_lane_prompts_are_covered_not_just_the_agentic_lane(self):
        legacy_prompts = (
            "01-thalamic-trajectory-factory.md",
            "02-multi-agent-ouroboros-swarm.md",
            "03-neuromorphic-event-language-bridge.md",
            "04-agentic-coding-trajectory-factory.md",
            "05-failure-as-fuel-preference-cascade.md",
        )
        for name in legacy_prompts:
            self.assertIn("Novel coverage: <N>%", self.prompts[name], name)
            self.assertIn("docs/token-efficiency.md", self.prompts[name], name)

    def test_the_contract_example_parses_with_the_shipped_regex(self):
        example = "Novel coverage: 12.3%"
        self.assertIn(example, self.prompts["_factory-contract.md"])
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

    def test_docs_and_prompts_agree_on_the_threshold(self):
        docs = DOCS.read_text()
        self.assertIn("Novel coverage: <N>%", docs)
        self.assertIn("5%", docs)
        for name, text in self.transactional.items():
            if "docs/token-efficiency.md" in text:
                self.assertIn("5%", text, name)


class RasterGateProducerContract(unittest.TestCase):
    """Every lane the publish gate holds to the raster contract must say so.

    ``round_txn.RASTER_FACTORY_SLUGS`` refuses a staged round whose records
    carry no ``raster`` / ``gate_snn`` sidecar. A producer that follows its
    prompt to the letter and still gets rejected would stall the lane, so the
    prompt for each gated lane has to name the sidecars and the schema.
    """

    @classmethod
    def setUpClass(cls):
        cls.prompts = {
            path.name: path.read_text(encoding="utf-8") for path in sorted(PROMPTS.glob("*.md"))
        }

    PROMPT_BY_SLUG = {
        "thalamic-trajectory-factory": "01-thalamic-trajectory-factory.md",
        "multi-agent-ouroboros-swarm": "02-multi-agent-ouroboros-swarm.md",
        "neuromorphic-event-language-bridge": ("03-neuromorphic-event-language-bridge.md"),
    }

    def test_every_gated_lane_has_a_prompt_that_documents_the_sidecars(self):
        self.assertEqual(
            sorted(round_txn.RASTER_FACTORY_SLUGS),
            sorted(self.PROMPT_BY_SLUG),
            "a lane joined the raster publish gate without a documented prompt",
        )
        for slug in sorted(round_txn.RASTER_FACTORY_SLUGS):
            name = self.PROMPT_BY_SLUG[slug]
            text = self.prompts[name]
            with self.subTest(prompt=name):
                self.assertIn("`raster`", text)
                self.assertIn("`gate_snn`", text)
                self.assertIn("schemas/raster.schema.json", text)

    def test_gate_compute_prompts_describe_all_carrier_validation(self):
        for name in (
            "01-thalamic-trajectory-factory.md",
            "02-multi-agent-ouroboros-swarm.md",
        ):
            text = " ".join(self.prompts[name].split())
            with self.subTest(prompt=name):
                self.assertIn("first declared carrier is selected", text)
                self.assertIn("every declared carrier", text)
                self.assertIn("any malformed declaration rejects the record", text)
                self.assertNotIn("first declared carrier is the one validated", text)

    def test_producer_prompts_describe_exact_derived_energy(self):
        for name in (
            "01-thalamic-trajectory-factory.md",
            "02-multi-agent-ouroboros-swarm.md",
        ):
            text = " ".join(self.prompts[name].split()).lower()
            with self.subTest(prompt=name):
                self.assertIn("omitted energy is allowed", text)
                self.assertIn("exact integer", text)
                self.assertIn("binary-double overflow", text)
                self.assertNotIn("not a finite double is rejected", text)


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
