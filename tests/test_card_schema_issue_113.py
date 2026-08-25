#!/usr/bin/env python3
"""Issue #53 leaf tests for the per-dataset card schema declaration."""

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


RATE_LIMIT = "rate-limit-backoff-trajectories"


RATE_LIMIT_GQL_MILL_IDS = (
    "gql-r135-hotchocolate-cost-analyzer-after-projection",
    "gql-r135-hotchocolate-disable-cost",
    "gql-r136-strawberry-relay-connection-after-override",
    "gql-r136-strawberry-drop-relay",
    "gql-r137-mercurius-persisted-query-after-schema",
    "gql-r137-mercurius-disable-persisted",
    "gql-r138-graphene-django-filter-after-queryset",
    "gql-r138-graphene-drop-filterset",
    "gql-r139-hasura-remote-schema-after-perm-reload",
    "gql-r139-hasura-disable-remote-schema",
)


RATE_LIMIT_SIR_MILL_IDS = (
    "sir-r114-quickwit-split-leftover3c-rebuild",
    "sir-r114-quickwit-drop-split-leftover3c-handoff",
)


RATE_LIMIT_THIN_META_IDS = (
    "rlb-r01-retry-after-seconds-ignored",
    "rlb-r01-retry-after-http-date-skew",
    "rlb-r02-reset-epoch-ignored",
    "rlb-r02-retry-after-zero-ms",
    "rlb-r07-http-503-retry-after-2d91",
    "rlb-r07-token-bucket-10rps-7e80",
    "rlb-r08-retry-after-zero-floor-5bb8",
    "rlb-r08-exp-min-retry-after-8d44",
)


class RateLimitBackoffDeclarationTests(unittest.TestCase):
    """Issue #53: thin `meta` on the earliest rounds plus optional `reward.mid_reward`.

    The counts asserted here were derived by scanning every published record in
    the read-only mirror at
    ``~/rmems/hf/grok-4.6/rate-limit-backoff-trajectories`` (312 records across
    156 shards, 5148 steps, 0 parse failures), not transcribed from the issue.
    """

    def setUp(self):
        self.declaration = card_schema.load(RATE_LIMIT)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #53")
        self.item = {
            "slug": "rate-limit-backoff-factory",
            "hub": RATE_LIMIT,
            "pretty": "Rate Limit Backoff Trajectories",
            "blurb": "API leftover-budget header vs naive-RPS episodes.",
            "tags": [
                "synthetic-data",
                "agentic-workflows",
                "grok-4.6",
                "provenance",
                "trajectories",
                "rate-limit",
            ],
        }
        self.card = publisher.render_card(
            self.item,
            records=312,
            bytes_=2426868,
            first="r01",
            last="r156",
            payload_names=["batch-r01.jsonl", "batch-r114.jsonl", "batch-r135.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        features = self.declaration["features"]
        self.assertEqual(
            [feature["name"] for feature in features],
            ["id", "goal", "plan", "steps", "outcome", "reward", "meta"],
        )
        names = {feature["name"]: feature for feature in features}
        # Every top-level field is on all 312 records: unlike the sibling dumps
        # nothing here is optional at the top level, `plan` included.
        for name, feature in names.items():
            with self.subTest(field=name):
                self.assertNotIn("optional", feature, f"{name} is on every record")
        # The two key-bags the viewer's cast died on.
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [53])

    def test_steps_keep_the_public_decision_basis_and_a_json_arg_bag(self):
        steps = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "steps"
        )
        children = {child["name"]: child for child in steps["list"]}
        self.assertEqual(
            set(children),
            {"n", "decision_basis", "tool_call", "observation", "reflection"},
        )
        self.assertEqual(children["n"]["dtype"], "int64")
        self.assertEqual(children["decision_basis"]["dtype"], "string")
        # 4831 of 5148 steps carry it; the rest read back as null.
        self.assertTrue(children["reflection"]["optional"])
        self.assertIn("4831 of 5148 steps", children["reflection"]["note"])
        tool_call = {child["name"]: child for child in children["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_reward_note_records_the_optional_mid_reward_count(self):
        names = {
            feature["name"]: feature for feature in self.declaration["features"]
        }
        # The issue's headline optional key: 136 of 312 records add it.
        self.assertIn("`mid_reward` on 136", names["reward"]["note"])
        self.assertIn("`handoff` / `xfailed` on 7", names["reward"]["note"])
        # `plant` and `lane` are the meta keys that no other record carries.
        self.assertIn("`plant` on 10", names["meta"]["note"])
        self.assertIn("`lane` on 8", names["meta"]["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("      - name: args\n        dtype: json\n", front_matter)
        # Card-only annotations must never be read back as a feature type.
        self.assertNotIn("optional", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_twelve_dest_stamped_mill_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("### Known payload disclosures", self.card)
        # Issue #53 claimed "no leftover-mill mix and no foreign factory"; the
        # mirror carries 10 `gql-` rows (#44's count) plus 2 `sir-` rows.
        for record_id in RATE_LIMIT_GQL_MILL_IDS + RATE_LIMIT_SIR_MILL_IDS:
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        for record_id in RATE_LIMIT_THIN_META_IDS:
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("issues/53", self.card)
        self.assertIn("issues/44", self.card)


if __name__ == "__main__":
    unittest.main()

