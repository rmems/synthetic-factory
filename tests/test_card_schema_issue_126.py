#!/usr/bin/env python3
"""Issue #64 leaf tests for the per-dataset card schema declaration."""

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


FLAKY_TEST_QUARANTINE = "flaky-test-quarantine-trajectories"


class FlakyTestQuarantineDeclarationTests(unittest.TestCase):
    """Issue #64: thin `meta` vs the later `designed` leftovers, plus 14 dest-stamped rows.

    Every count asserted here was derived from the read-only mirror at
    `~/rmems/hf/grok-4.6/flaky-test-quarantine-trajectories` (1575 shards,
    3150 records, 38604 steps, 0 parse failures).
    """

    SIR_IDS = (
        "sir-r1537-weaviate-alias-leftover-lll-rebuild",
        "sir-r1537-weaviate-drop-class-leftover-lll-handoff",
        "sir-r1538-qdrant-alias-leftover-lll-rebuild",
        "sir-r1538-qdrant-delete-coll-leftover-lll-handoff",
        "sir-r1539-milvus-alias-leftover-lll-rebuild",
        "sir-r1539-milvus-drop-coll-leftover-lll-handoff",
        "sir-r1540-pinecone-ns-leftover-lll-rebuild",
        "sir-r1540-pinecone-delete-index-leftover-lll-handoff",
        "sir-r1541-chroma-persist-leftover-lll-rebuild",
        "sir-r1541-chroma-delete-coll-leftover-lll-handoff",
        "sir-r1542-lancedb-compact-leftover-lll-rebuild",
        "sir-r1542-lancedb-overwrite-leftover-lll-handoff",
        "sir-r1543-pgvector-hnsw-leftover-lll-rebuild",
        "sir-r1543-pgvector-drop-hnsw-leftover-lll-handoff",
    )

    def setUp(self):
        self.declaration = card_schema.load(FLAKY_TEST_QUARANTINE)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #64")
        self.item = {
            "slug": "flaky-test-quarantine-factory",
            "hub": FLAKY_TEST_QUARANTINE,
            "pretty": "Flaky Test Quarantine Trajectories",
            "blurb": "Flaky-test leftover-cause quarantine episodes.",
            "tags": ["synthetic-data", "trajectories", "testing", "flaky-tests"],
        }
        self.card = publisher.render_card(
            self.item,
            records=3150,
            bytes_=12326850,
            first="r01",
            last="r1575",
            payload_names=[f"batch-r{n}.jsonl" for n in range(1, 1576)],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            list(names),
            ["id", "goal", "plan", "steps", "outcome", "reward", "meta"],
        )
        self.assertEqual(self.declaration["issues"], [64])
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_plan_is_mandatory_here_unlike_the_worked_example(self):
        # 3150 of 3150 records carry a string `plan`. Optionality is derived from
        # this dump, never copied from `long-horizon-coding-trajectories`.
        plan = next(f for f in self.declaration["features"] if f["name"] == "plan")
        self.assertNotIn("optional", plan)
        self.assertEqual(plan["dtype"], "string")
        long_horizon = card_schema.load(LONG_HORIZON)
        borrowed = next(f for f in long_horizon["features"] if f["name"] == "plan")
        self.assertTrue(borrowed["optional"])

    def test_only_step_reflection_is_optional(self):
        rows = card_schema.field_notes(self.declaration["features"])
        optional = [path for path, is_optional, _note in rows if is_optional]
        self.assertEqual(optional, ["steps[].reflection"])
        self.assertIn("6586 of 38604 steps", dict((p, n) for p, _o, n in rows)[
            "steps[].reflection"
        ])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_reward_note_names_the_variants_the_issue_census_omitted(self):
        reward = next(f for f in self.declaration["features"] if f["name"] == "reward")
        # Derived from the mirror: issue #64 lists 13 keys plus `drop_flag_*`;
        # these three key variants are real and were missing from that census.
        for key in ("skip_applied", "repeats_ok", "locales_ok"):
            with self.subTest(key=key):
                self.assertIn(f"`{key}`", reward["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("      - name: args\n        dtype: json\n", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertNotIn("optional", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_every_dest_stamped_leftover(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        for record_id in self.SIR_IDS:
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("98 calls total: 42 `pytest` and 56 `fetch`", self.card)
        self.assertIn("across the 231 steps in those episodes", self.card)
        self.assertNotIn("tool calls (231 of", self.card)

    def test_disclosures_keep_ownership_and_separate_the_advertised_mechanic(self):
        summaries = [d["summary"] for d in self.declaration["disclosures"]]
        joined = " ".join(summaries)
        sir = next(d for d in self.declaration["disclosures"] if d["ids"])
        self.assertEqual(list(sir["ids"]), list(self.SIR_IDS))
        self.assertEqual(sir["issues"], [64])
        # The 14 belong to neither frozen census, so #64 must own them.
        self.assertIn("issue 43", joined)
        self.assertIn("issue 44", joined)
        # This factory's own leftover-* naming must not be sold as a foreign dump.
        self.assertIn("advertised mechanic", joined)
        self.assertIn("3136", joined)


if __name__ == "__main__":
    unittest.main()
