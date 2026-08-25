#!/usr/bin/env python3
"""Issue #57 leaf tests for the per-dataset card schema declaration."""

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


CACHE_STAMPEDE = "cache-stampede-trajectories"


class CacheStampedeDeclarationTests(unittest.TestCase):
    """Issue #57: thin `meta` vs the designed / dest-stamped union on this dump."""

    def setUp(self):
        self.declaration = card_schema.load(CACHE_STAMPEDE)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #57")
        self.item = {
            "slug": "cache-stampede-factory",
            "hub": CACHE_STAMPEDE,
            "pretty": "Cache Stampede Trajectories",
            "blurb": "Cache stampede leftover-key / lock / singleflight episodes.",
            "tags": ["synthetic-data", "cache", "stampede"],
        }
        # Counts derived from the 1728-shard local mirror: 3456 records,
        # 50403 steps, 0 parse failures.
        self.card = publisher.render_card(
            self.item,
            records=3456,
            bytes_=20725966,
            first="r01",
            last="r1728",
            payload_names=["batch-r01.jsonl", "batch-r1401.jsonl", "batch-r1728.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # `plan` is on all 3456 records here, unlike the #36 dataset.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertEqual(steps["n"]["dtype"], "int64")
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("5029 of 50403", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [57])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_the_default_config_covers_every_published_shard(self):
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration,
                [f"batch-r{index:02d}.jsonl" for index in range(1, 1729)],
            ),
            [],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("      - name: args\n        dtype: json\n", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)

    def test_card_body_attributes_each_dest_stamped_class_to_its_owner(self):
        self.assertIn("## Dataset viewer schema", self.card)
        # The 18 rows owned by #44 -- disclosed, not re-filed.
        self.assertIn("issues/44", self.card)
        self.assertIn("`gql-r1405-postgraphile-drop-wrap`", self.card)
        self.assertIn("`dbc-r1413-overlayfs-opaque-xattr-l3`", self.card)
        # The 8 search-index leftover3c rows -- disclosed, no new mill issue.
        self.assertIn("`sir-r1401-manticore-rt-leftover3c-rebuild`", self.card)
        self.assertIn("`sir-r1404-solr-drop-core-leftover3c-handoff`", self.card)

    def test_card_body_does_not_misreport_the_advertised_leftover_mechanic(self):
        self.assertIn(
            "387 of the 3430 `cst-*` records carry `leftover` in the record id",
            self.card,
        )
        self.assertIn("advertised cache leftover-key mechanic", self.card)
        self.assertIn("not a MIXED-kind signal", self.card)

    def test_card_body_reports_the_optional_and_key_bag_fields(self):
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)
        self.assertIn("`steps[].tool_call.args`, `reward`, `meta`", self.card)
        self.assertIn("no hidden `thought` or `internal_reasoning`", self.card)


if __name__ == "__main__":
    unittest.main()

