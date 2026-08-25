#!/usr/bin/env python3
"""Issue #67 leaf tests for the per-dataset card schema declaration."""

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


INFRA_AS_CODE = "infra-as-code-trajectories"


class InfraAsCodeDeclarationTests(unittest.TestCase):
    """Issue #67: thin `meta` vs the `plant` / `kind` rounds kills the cast."""

    def setUp(self):
        self.declaration = card_schema.load(INFRA_AS_CODE)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #67")
        self.item = {
            "slug": "infra-as-code-factory",
            "hub": INFRA_AS_CODE,
            "pretty": "Infra As Code Trajectories",
            "blurb": "Terraform/Kubernetes leftover-object IaC repair.",
            "tags": ["synthetic-data", "trajectories", "terraform", "kubernetes", "iac"],
        }
        self.card = publisher.render_card(
            self.item,
            records=2832,
            bytes_=18113106,
            first="r01",
            last="r1416",
            payload_names=["batch-r01.jsonl", "batch-r1416.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # `plan` is a string on all 2832 records here; the worked example's
        # optional `plan` must not be copied over.
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("17436 of 48350", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [67])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_meta_note_records_the_split_the_viewer_dies_on(self):
        meta = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "meta"
        )
        # 1814 thin + 1018 wide = 2832 records; the wide rounds are contiguous.
        for fragment in ("1018", "78-586", "1814", "1-77", "587-1416", "sim_or_real"):
            self.assertIn(fragment, meta["note"])

    def test_reward_note_names_the_only_type_varying_key(self):
        reward = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "reward"
        )
        # `handoff` is the single int-or-string key; the tests_* counters are not.
        self.assertIn("`handoff` is the only key whose value type varies", reward["note"])
        for singleton in ("wrong_cluster_apply", "replicas", "targets_healthy"):
            self.assertIn(singleton, reward["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: plan\n    dtype: string\n", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_owns_the_leftover_mechanic_without_claiming_a_mill(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)
        # The 13 string-valued handoff ids are named on the card.
        self.assertIn("`iac-r03-b-helm-reuse-values-tag-drift`", self.card)
        self.assertIn("`iac-r27-b-helm-history-max-zero`", self.card)
        # Same-factory leftover naming is disclosed as the advertised mechanic,
        # and the inbound-mill disclosure defers to the destination dumps.
        self.assertIn("advertised mechanic", self.card)
        self.assertIn("There is no inbound leftover mill in this dataset", self.card)
        self.assertIn("/issues/43", self.card)
        self.assertIn("/issues/44", self.card)


if __name__ == "__main__":
    unittest.main()

