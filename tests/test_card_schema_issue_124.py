#!/usr/bin/env python3
"""Issue #61 leaf tests for the per-dataset card schema declaration."""

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

DOCKER_BUILD_CACHE_MIRROR = (
    Path.home()
    / "rmems"
    / "hf"
    / "grok-4.6"
    / "docker-build-cache-trajectories"
    / "data"
    / "raw"
)


class DockerBuildCacheDeclarationTests(unittest.TestCase):
    """Issue #61: thin `meta` vs the `plant` / `designed` leftover shapes.

    Every count asserted here was derived from the published mirror
    (1028 shards, 2056 records, 36640 steps, 0 parse failures), not copied
    from the issue text.
    """

    DATASET = "docker-build-cache-trajectories"

    def setUp(self):
        self.declaration = card_schema.load(self.DATASET)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #61")
        self.item = {
            "slug": "docker-build-cache-factory",
            "hub": self.DATASET,
            "pretty": "Docker Build Cache Trajectories",
            "blurb": "Docker/BuildKit leftover cache-invalidation episodes.",
            "tags": ["synthetic-data", "trajectories", "docker", "buildkit", "cache"],
        }
        self.card = publisher.render_card(
            self.item,
            records=2056,
            bytes_=12548477,
            first="r01",
            last="r1028",
            payload_names=[f"batch-r{n}.jsonl" for n in range(1, 1029)],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        expected_yaml_features = [
            {"name": "id", "dtype": "string"},
            {"name": "goal", "dtype": "string"},
            {"name": "plan", "dtype": "string"},
            {
                "name": "steps",
                "list": [
                    {"name": "n", "dtype": "int64"},
                    {"name": "decision_basis", "dtype": "string"},
                    {
                        "name": "tool_call",
                        "struct": [
                            {"name": "name", "dtype": "string"},
                            {"name": "args", "dtype": "json"},
                        ],
                    },
                    {"name": "observation", "dtype": "string"},
                    {"name": "reflection", "dtype": "string"},
                ],
            },
            {"name": "outcome", "dtype": "string"},
            {"name": "reward", "dtype": "json"},
            {"name": "meta", "dtype": "json"},
        ]
        self.assertEqual(
            card_schema.yaml_features(self.declaration["features"]),
            expected_yaml_features,
        )
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [61])

    def test_plan_is_mandatory_here_unlike_the_sibling_declaration(self):
        """`plan` is on 2056 of 2056 records; optionality is never inherited."""
        plan = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "plan"
        )
        self.assertEqual(plan["dtype"], "string")
        self.assertNotIn("optional", plan)
        self.assertIn("2056 of 2056", plan["note"])
        sibling = card_schema.load(LONG_HORIZON)
        sibling_plan = next(
            feature for feature in sibling["features"] if feature["name"] == "plan"
        )
        self.assertTrue(sibling_plan["optional"])
        self.assertIn("| `plan` | present on every record |", self.card)

    @unittest.skipUnless(
        DOCKER_BUILD_CACHE_MIRROR.is_dir(),
        "read-only published mirror is not available",
    )
    def test_published_mirror_has_a_nonempty_plan_on_every_record(self):
        """Recheck the declaration's nullability claim when the mirror is present."""
        payloads = sorted(DOCKER_BUILD_CACHE_MIRROR.glob("batch-*.jsonl"))
        self.assertEqual(len(payloads), 1028)
        records = 0
        for payload in payloads:
            with payload.open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    plan = record.get("plan")
                    self.assertIsInstance(plan, str, f"{payload.name}:{line_number}")
                    self.assertTrue(plan.strip(), f"{payload.name}:{line_number}")
                    records += 1
        self.assertEqual(records, 2056)

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        # Parent tests pin the stdlib YAML emitter byte-for-byte. This leaf
        # asserts that the complete structurally validated block is inserted
        # once, at the end of the card front matter.
        emitted = card_schema.metadata_yaml(self.declaration)
        self.assertEqual(front_matter.count("configs:\n"), 1)
        self.assertEqual(front_matter.count("dataset_info:\n"), 1)
        self.assertTrue(front_matter.endswith(emitted))
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        # `n` is a YAML boolean unless quoted, so the step index must stay a string.
        self.assertIn('    - name: "n"\n      dtype: int64\n', front_matter)
        # No card-only annotation may reach the YAML: `datasets` reads the
        # feature type from the first key after `name`.
        self.assertNotIn("optional:", front_matter)
        self.assertNotIn("note:", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_owns_the_designed_l3_records_and_the_leftover_mechanic(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        # The advertised same-factory leftover-cache mechanic, not a foreign dump.
        self.assertIn("833 of the 2056 record ids contain `leftover`", self.card)
        # The 26 designed cache-product templates are owned here by name.
        self.assertIn("`dbc-r634-bk-cachemount-id-alias-l3`", self.card)
        self.assertIn("`dbc-r646-containerd-gc-root-label-l3`", self.card)
        # Outbound copies in destination dumps stay with #44, not with this card.
        self.assertIn("/issues/44", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("696 of 36640 steps", self.card)

    def test_disclosures_keep_every_record_with_this_factory(self):
        summaries = [item["summary"] for item in self.declaration["disclosures"]]
        joined = " ".join(summaries)
        self.assertIn("no dest-stamped foreign payload", joined)
        self.assertIn("36640 of 36640", joined)
        listed = {
            record_id
            for item in self.declaration["disclosures"]
            for record_id in item["ids"]
        }
        # 26 designed `-l3` ids plus the 8 single-record `reward` extras.
        self.assertEqual(len(listed), 34)
        self.assertEqual(
            sum(1 for record_id in listed if record_id.endswith("-l3")), 26
        )
        self.assertTrue(all(record_id.startswith("dbc-") for record_id in listed))


if __name__ == "__main__":
    unittest.main()
