#!/usr/bin/env python3
"""PR #133 / issue #72 leaf tests for the per-dataset card schema declaration."""

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


SEARCH_INDEX_REBUILD = "search-index-rebuild-trajectories"


SIR_THIN_META_IDS = (
    "sir-r01-es-mapping-conflict-reindex",
    "sir-r01-alias-swap-old-index-leftover",
    "sir-r05-meili-swap-filterable-5bb8",
    "sir-r05-typesense-alias-facet-8d44",
    "sir-r06-manticore-attach-rt-a091",
    "sir-r06-sonic-flushb-then-push-7e80",
)


SIR_LANE_IDS = (
    "sir-r2-os-alias-swap-p5",
    "sir-r2-solr-tlog-p5",
    "sir-r3-os-alias-swap-p5",
    "sir-r3-solr-tlog-p5",
    "sir-r4-os-alias-swap-p15",
    "sir-r4-solr-tlog-p15",
)


class SearchIndexRebuildDeclarationTests(unittest.TestCase):
    """PR #133 / issue #72: thin `meta` vs the designed/lane union schema.

    Numbers below are the counted union over the 250 published records in
    ``data/raw/batch-r01.jsonl`` .. ``batch-r125.jsonl`` (4123 steps).
    """

    def setUp(self):
        self.declaration = card_schema.load(SEARCH_INDEX_REBUILD)
        self.assertIsNotNone(
            self.declaration,
            "PR #133 is missing the config/card-schemas declaration for issue #72",
        )
        self.item = {
            "slug": "search-index-rebuild-factory",
            "hub": SEARCH_INDEX_REBUILD,
            "pretty": "Search Index Rebuild Trajectories",
            "blurb": "Search leftover-segment / schema rebuild episodes.",
            "tags": ["synthetic-data", "trajectories", "search", "indexing"],
        }
        self.card = publisher.render_card(
            self.item,
            records=250,
            bytes_=1525810,
            first="r01",
            last="r125",
            payload_names=[f"batch-r{n:02d}.jsonl" for n in range(1, 126)],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        self.assertEqual(self.declaration["issues"], [72])
        self.assertEqual(self.declaration["config_name"], "default")
        self.assertEqual(self.declaration["split"], "train")
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_plan_is_a_mandatory_string_here_not_an_optional_field(self):
        # The worked example (#36) declares `plan` optional. In this dataset it is
        # a string on all 250 records, so declaring it optional would be a lie.
        plan = next(f for f in self.declaration["features"] if f["name"] == "plan")
        self.assertEqual(plan["dtype"], "string")
        self.assertNotIn("optional", plan)
        self.assertIn("| `plan` | present on every record |", self.card)

    def test_only_the_three_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("      - name: args\n        dtype: json\n", front_matter)
        # Card-only annotations must never reach the YAML.
        self.assertNotIn("optional", front_matter)
        self.assertNotIn("note:", front_matter)
        # License / status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_thin_meta_lane_and_stub_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("issues/72", self.card)
        self.assertIn("### Known payload disclosures", self.card)
        for record_id in SIR_THIN_META_IDS + SIR_LANE_IDS:
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("`sir-r26-typesense-synonym-used`", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("4038 of 4123 steps", self.card)

    def test_card_owns_the_same_factory_leftover_naming_without_claiming_a_mix(self):
        self.assertIn("leftover-segment", self.card)
        self.assertIn("109 of 250 ids", self.card)
        self.assertIn("no dest-stamped foreign payload in this dataset", self.card)
        self.assertIn("decision_basis", self.card)

    def test_the_declared_glob_covers_every_published_shard(self):
        every_shard = [f"batch-r{n:02d}.jsonl" for n in range(1, 126)]
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, every_shard), []
        )
        self.assertTrue(
            card_schema.payload_coverage_errors(
                self.declaration, every_shard + ["episodes.jsonl"]
            )
        )


if __name__ == "__main__":
    unittest.main()
