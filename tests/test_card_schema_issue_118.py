#!/usr/bin/env python3
"""Issue #56 leaf tests for the per-dataset card schema declaration."""

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


AUTHZ_REGRESSION = "authz-regression-trajectories"


class AuthzRegressionDeclarationTests(unittest.TestCase):
    """Issue #56: thin `meta` vs designed/domain/stack plus reward extras.

    Every count asserted here was derived by scanning the untouched public
    mirror at ``~/rmems/hf/grok-4.6/authz-regression-trajectories``: 3518
    records over 1759 shards, 59188 steps, 0 parse failures.
    """

    def setUp(self):
        self.declaration = card_schema.load(AUTHZ_REGRESSION)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #56")
        self.item = {
            "slug": "authz-regression-factory",
            "hub": AUTHZ_REGRESSION,
            "pretty": "Authz Regression Trajectories",
            "blurb": "Authorization IDOR / BFLA leftover-mechanic episodes.",
            "tags": ["synthetic-data", "trajectories", "authz", "security", "idor"],
        }
        self.card = publisher.render_card(
            self.item,
            records=3518,
            bytes_=21248000,
            first="r01",
            last="r1759",
            payload_names=["batch-r01.jsonl", "batch-r1459.jsonl", "batch-r1759.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta", "state"},
        )
        # `plan` is on all 3518 records here, unlike the #36 dataset.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("7181 of 59188 steps", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [56])

    def test_state_is_optional_and_declared_as_a_uniform_struct(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        state = names["state"]
        self.assertTrue(state["optional"])
        self.assertIn("480 of 3518", state["note"])
        # All 480 carry both keys with constant string values, so `state` is a
        # castable struct rather than a key-bag; it stays out of the json set.
        self.assertEqual(
            [child["name"] for child in state["struct"]], ["sim_or_real", "domain"]
        )
        self.assertEqual(
            {child["dtype"] for child in state["struct"]}, {"string"}
        )

    def test_key_bag_columns_are_declared_json(self):
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
        self.assertIn(
            "  - name: state\n    struct:\n    - name: sim_or_real\n", front_matter
        )
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_ten_dest_stamped_leftovers(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertIn("`sir-r1459-sqlite-vec-veci-leftover-lll-rebuild`", self.card)
        self.assertIn("`sir-r1463-os-drop-ism-leftover-lll-handoff`", self.card)
        self.assertIn("| `state` | optional |", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("/issues/43", self.card)
        self.assertIn("/issues/44", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)

    def test_card_body_states_the_derived_reward_split(self):
        # The reward extras are not the leftover-mill discriminator: 575 of the
        # 580 handoff/xfailed rows are ordinary `azr-*` episodes, and `retries`
        # is the key that is confined to the 5 dest-stamped rebuild rows.
        self.assertIn("575 of those 580 are ordinary `azr-*`", self.card)
        self.assertIn("5 `sir-*-rebuild` rows", self.card)


if __name__ == "__main__":
    unittest.main()

