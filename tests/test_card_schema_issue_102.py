#!/usr/bin/env python3
"""Issue #39 leaf tests for the per-dataset card schema declaration."""

import test_card_schema as _shared

unittest = _shared.unittest
io = _shared.io
json = _shared.json
tempfile = _shared.tempfile
redirect_stderr = _shared.redirect_stderr
redirect_stdout = _shared.redirect_stdout
Path = _shared.Path
mock = _shared.mock
REPO = _shared.REPO
card_schema = _shared.card_schema
publisher = _shared.publisher
LONG_HORIZON = _shared.LONG_HORIZON
MINIMAL = _shared.MINIMAL
write_declaration = _shared.write_declaration


BROWSER_TOOL_USE = "browser-tool-use-trajectories"


BROWSER_LEFTOVER_MILL_IDS = (
    "obs-r649-lightstep-max-spans-zero-leftover",
    "obs-r649-chrono-drop-metric-name-leftover",
    "sir-r650-meili-swap-leftover3c-rebuild",
    "sir-r650-meili-drop-index-leftover3c-handoff",
    "sir-r651-typesense-alias-leftover3c-rebuild",
    "sir-r651-typesense-drop-coll-leftover3c-handoff",
    "sir-r652-sonic-push-leftover3c-rebuild",
    "sir-r652-sonic-drop-bucket-leftover3c-handoff",
    "sir-r653-tantivy-commit-leftover3c-rebuild",
    "sir-r653-tantivy-drop-writer-leftover3c-handoff",
)


class BrowserToolUseDeclarationTests(unittest.TestCase):
    """Issue #39: reward key-bag drift plus ten leftover-mill records.

    Every count asserted here was derived read-only from the published mirror
    `~/rmems/hf/grok-4.6/browser-tool-use-trajectories` (1111 payloads, 2222
    records, 29707 steps, 0 parse failures). The assertions are hermetic: they
    pin the declaration, so a later hand edit that drifts from the scan is
    caught without the test reaching outside the repository.
    """

    def setUp(self):
        self.declaration = card_schema.load(BROWSER_TOOL_USE)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #39")
        self.item = {
            "slug": "browser-tool-use-factory",
            "hub": BROWSER_TOOL_USE,
            "pretty": "Browser Tool Use Trajectories",
            "blurb": "Browser selector-fail/retry episodes.",
            "tags": ["synthetic-data", "trajectories"],
        }
        self.card = publisher.render_card(
            self.item,
            records=2222,
            bytes_=10285056,
            first="01",
            last="1111",
            payload_names=["batch-r01.jsonl", "batch-r649.jsonl", "batch-r653.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        features = self.declaration["features"]
        self.assertEqual(
            [feature["name"] for feature in features],
            ["id", "goal", "plan", "steps", "outcome", "reward", "meta"],
        )
        names = {feature["name"]: feature for feature in features}
        # All 2222 records share one top-level key set, so -- unlike #36 --
        # `plan` is present on every record and must not be marked optional.
        for name, feature in names.items():
            with self.subTest(field=name):
                self.assertFalse(feature.get("optional", False))
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [39])

    def test_step_schema_marks_only_reflection_optional(self):
        top = {feature["name"]: feature for feature in self.declaration["features"]}
        steps = {feature["name"]: feature for feature in top["steps"]["list"]}
        self.assertEqual(
            list(steps), ["n", "decision_basis", "tool_call", "observation", "reflection"]
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("2991 of 29707 steps", steps["reflection"]["note"])
        for name in ("n", "decision_basis", "tool_call", "observation"):
            with self.subTest(field=name):
                self.assertFalse(steps[name].get("optional", False))
        tool_call = {f["name"]: f for f in steps["tool_call"]["struct"]}
        self.assertEqual(list(tool_call), ["name", "args"])
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_every_type_varying_column_is_declared_json(self):
        # `reward`, `meta` and `tool_call.args` are the three key bags; nothing
        # else in this dataset varies, so nothing else should be `json`.
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_note_names_the_reward_keys_the_inferred_cast_died_on(self):
        note = self.declaration["note"]
        self.assertIn("reward", note)
        self.assertIn("http_403s", note)
        self.assertIn("pager_last_row_still_broken", note)

    def test_default_batch_glob_covers_every_published_payload(self):
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])
        # The mirror publishes only `batch-rNNNN.jsonl`; there is no legacy
        # `episodes.jsonl` in this factory, so the default glob is complete.
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration,
                ["batch-r01.jsonl", "batch-r649.jsonl", "batch-r1111.jsonl"],
            ),
            [],
        )
        self.assertTrue(
            card_schema.payload_coverage_errors(self.declaration, ["episodes.jsonl"])
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("      - name: args\n        dtype: json\n", front_matter)
        # A required field must not leak the card-only annotations.
        self.assertNotIn("optional", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_all_ten_foreign_leftover_records(self):
        disclosed = {
            record_id
            for disclosure in self.declaration["disclosures"]
            for record_id in disclosure["ids"]
        }
        self.assertEqual(disclosed, set(BROWSER_LEFTOVER_MILL_IDS))
        self.assertIn("### Known payload disclosures", self.card)
        for record_id in BROWSER_LEFTOVER_MILL_IDS:
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("search-index-rebuild-factory", self.card)
        self.assertIn("observability-debug-factory", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)


if __name__ == "__main__":
    unittest.main()

