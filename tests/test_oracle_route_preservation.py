"""Oracle source bytes and oracle validation outrank generic representations."""

import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
import curate_identity as identity
import validate_run
from curate_agentic_fixtures import episode_fixture
from test_oracle_curation_wiring import SOURCE_PATH, _build


class OracleRoutePreservation(unittest.TestCase):
    def test_digestless_original_line_is_preserved_in_identity_mapping(self):
        item = _build()
        original = json.dumps(item, separators=(", ", " : "), ensure_ascii=False)
        result = identity.curate_record(identity.SourceRecord(
            record=item, source_path=SOURCE_PATH, source_line=1, source_json=original,
        ), registry=identity.default_registry())
        self.assertEqual(result.action, "retained")
        source = result.mapping["source"]
        self.assertEqual(source["original"], original)
        self.assertEqual(source["sha256"], hashlib.sha256(original.encode()).hexdigest())
        self.assertEqual(source["hash_basis"], "source-json-line-sha256")

    def test_oracle_envelopes_cannot_hide_behind_valid_episode_fields(self):
        for mutation in ("tampered-result", "missing-oracle", "tampered-schema"):
            with self.subTest(mutation=mutation):
                item = _build()
                episode = episode_fixture()
                item.update({key: episode[key] for key in ("goal", "steps", "outcome", "reward")})
                if mutation == "missing-oracle":
                    item.pop("oracle")
                elif mutation == "tampered-schema":
                    item["schema"] = "forged"
                else:
                    item["result_hash"] = "sha256:" + "0" * 64
                self.assertEqual(validate_run.check_episode(item, "record"), [])
                errors, kind = validate_run.check_line(item, "accepted-r01.jsonl:1")
                self.assertEqual(kind, "oracle")
                self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
