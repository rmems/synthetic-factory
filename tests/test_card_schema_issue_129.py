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
INFRA_AS_CODE_MIRROR = (
    Path.home() / "rmems" / "hf" / "grok-4.6" / INFRA_AS_CODE / "data" / "raw"
)


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
            records=5208,
            bytes_=29388051,
            first="r01",
            last="r2604",
            payload_names=["batch-r01.jsonl", "batch-r1416.jsonl", "batch-r2604.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # `plan` is a string on all 5208 records here; the worked example's
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
        self.assertIn("17436 of 87554", steps["reflection"]["note"])
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
        # 4190 thin + 1018 wide = 5208 records; the wide rounds are contiguous.
        for fragment in ("1018", "78-586", "4190", "1-77", "587-2604", "sim_or_real"):
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

    @unittest.skipUnless(
        INFRA_AS_CODE_MIRROR.is_dir(),
        "read-only published mirror is not available",
    )
    def test_published_mirror_reconciles_the_post_r1416_growth(self):
        """Re-derive the declared censuses from the mirror at the r2604 frontier.

        Rounds 1417-2604 were published on 2026-08-26, after the issue #67
        census was derived at the r1416 frontier. This reconciliation fails on
        any declaration still carrying the r1416-frontier totals and pins the
        claim that the growth widened nothing: no new reward key, no new tool,
        no new arg key, and no `reflection` outside rounds 1-1416.
        """
        payloads = sorted(INFRA_AS_CODE_MIRROR.glob("batch-*.jsonl"))
        self.assertEqual(len(payloads), 2604)
        records = []
        for payload in payloads:
            with payload.open(encoding="utf-8") as handle:
                rows = [json.loads(line) for line in handle if line.strip()]
            self.assertEqual(len(rows), 2, payload.name)
            records.extend(rows)
        self.assertEqual(len(records), 5208)
        self.assertEqual(len({record["id"] for record in records}), 5208)

        steps = [step for record in records for step in record["steps"]]
        self.assertEqual(len(steps), 87554)
        reflections = [
            record["meta"]["round"]
            for record in records
            for step in record["steps"]
            if "reflection" in step
        ]
        self.assertEqual(len(reflections), 17436)
        self.assertLessEqual(max(reflections), 1416)

        thin = sum(
            1
            for record in records
            if set(record["meta"]) == {"factory", "generator", "round"}
        )
        wide_rounds = sorted(
            record["meta"]["round"] for record in records if "kind" in record["meta"]
        )
        self.assertEqual(thin, 4190)
        self.assertEqual(len(wide_rounds), 1018)
        self.assertEqual((wide_rounds[0], wide_rounds[-1]), (78, 586))

        handoff_types = {}
        reward_counts = {}
        for record in records:
            for key, value in record["reward"].items():
                reward_counts[key] = reward_counts.get(key, 0) + 1
                if key == "handoff":
                    kind = type(value).__name__
                    handoff_types[kind] = handoff_types.get(kind, 0) + 1
        self.assertEqual(reward_counts["tests_passed"], 5180)
        self.assertEqual(reward_counts["handoff"], 2606)
        self.assertEqual(reward_counts["tests_failed"], 2576)
        self.assertEqual(handoff_types, {"int": 2593, "str": 13})

        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertIn(f"on all {len(records)} records", names["meta"]["note"])
        self.assertIn(f"`handoff` on {reward_counts['handoff']}", names["reward"]["note"])
        reflection = next(
            feature
            for feature in names["steps"]["list"]
            if feature["name"] == "reflection"
        )
        self.assertIn(f"{len(reflections)} of {len(steps)}", reflection["note"])

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
