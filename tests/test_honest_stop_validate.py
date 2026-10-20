"""Structural checks for honest-stop records, including the handwritten fixtures."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import honest_stop.vocabulary as cv
from honest_stop.records import build_record
from honest_stop.validate import validate_record, validate_text

FIXTURES = REPO / "tests" / "fixtures" / "honest-stop"
PRODUCED_AT = "2026-10-20T23:00:00Z"
SCHEMA = REPO / "schemas" / "agent-honest-stop-episode-v1.schema.json"


def built(scenario_id: str = "missing-credential") -> dict:
    return build_record(scenario_id, produced_at=PRODUCED_AT, run_seed=1)


class ValidatorTests(unittest.TestCase):
    def test_builder_record_is_structurally_valid(self):
        self.assertEqual(validate_record(built()), ())

    def test_handwritten_fixture_requires_counterfactual(self):
        text = (FIXTURES / "missing-counterfactual.json").read_text(encoding="utf-8")
        self.assertEqual(validate_text(text), ("counterfactual_fake_success",))

    def test_blank_counterfactual_is_rejected(self):
        record = built()
        record["counterfactual_fake_success"] = "   "
        self.assertEqual(validate_record(record), ("counterfactual_fake_success",))

    def test_handwritten_fixture_rejects_action_type_outside_the_enum(self):
        text = (FIXTURES / "bad-action-type.json").read_text(encoding="utf-8")
        self.assertEqual(validate_text(text), ("correct_action.type",))

    def test_provenance_is_required(self):
        record = built()
        del record["provenance"]
        self.assertEqual(validate_record(record), ("provenance",))

    def test_provenance_object_must_carry_its_fields(self):
        record = built()
        record["provenance"] = {}
        self.assertEqual(validate_record(record), ("provenance",))

    def test_duplicate_keys_are_rejected(self):
        text = (FIXTURES / "duplicate-key.json").read_text(encoding="utf-8")
        self.assertEqual(validate_text(text), ("record.json",))

    def test_extra_key_is_rejected(self):
        record = built()
        record["thought"] = "hidden"
        self.assertEqual(validate_record(record), ("record.keys",))

    def test_boolean_is_not_an_integer_seed(self):
        record = built()
        record["context"]["seed"] = True
        self.assertIn("context.seed", validate_record(record))

    def test_schema_required_fields_and_action_enum_match_the_validator(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), set(cv.RECORD_KEYS))
        self.assertIn("counterfactual_fake_success", schema["required"])
        self.assertIn("provenance", schema["required"])
        enum = schema["properties"]["correct_action"]["properties"]["type"]["enum"]
        self.assertEqual(set(enum), set(cv.ACTION_TYPES))
        self.assertFalse(schema["additionalProperties"])

    def test_import_twins_share_one_module(self):
        script = (
            "import sys\n"
            f"sys.path[:0] = [{str(PIPELINES)!r}, {str(REPO)!r}]\n"
            "import honest_stop.validate as flat\n"
            "import pipelines.honest_stop.validate as packaged\n"
            "assert flat is packaged\n"
        )
        done = subprocess.run(
            [sys.executable, "-c", script],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(done.returncode, 0, done.stderr)


if __name__ == "__main__":
    unittest.main()
