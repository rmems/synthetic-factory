"""Generator validation retains bindings captured before live callbacks."""

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import record  # noqa: E402


class CapturedGeneratorBindingsTest(unittest.TestCase):
    def setUp(self):
        root = REPO / "tests/fixtures/oracle-grounded/golden-r01"
        source = sorted(root.glob("*/accepted-*.jsonl"))[0]
        self.item = json.loads(source.read_text().splitlines()[0])

    def test_proposal_callback_cannot_replace_captured_family_for_metadata(self):
        original_spec_for = record.families.spec_for

        def spec_for(family):
            spec = original_spec_for(family)

            def propose(rng):
                proposal = spec.propose(rng)
                self.item["family"] = "changed-by-callback"
                return proposal

            return SimpleNamespace(propose=propose, build_request=spec.build_request)

        with mock.patch.object(record.families, "spec_for", side_effect=spec_for):
            findings = record._validate_generator_side(self.item)
        self.assertEqual(findings, [
            "oracle request could not be rebuilt from scenario and intervention: KeyError"
        ])

    def test_identifier_callback_cannot_replace_captured_generator(self):
        original_match = record.re.fullmatch

        def fullmatch(*args, **kwargs):
            match = original_match(*args, **kwargs)
            self.item["generator"] = {"seed": None}
            return match

        with mock.patch.object(record.re, "fullmatch", side_effect=fullmatch):
            findings = record._validate_generator_side(self.item)
        self.assertEqual(findings, [
            "proposal_hash does not cover the stored generator sections "
            "(the scenario or the prediction was edited after the oracle ran)"
        ])


if __name__ == "__main__":
    unittest.main()
