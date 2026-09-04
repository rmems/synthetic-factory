#!/usr/bin/env python3
"""Issue #45 leaf tests for the per-dataset card schema declaration."""

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


SPARSE_REWARD = "sparse-reward-long-tasks"

# The Hub item and published-payload facts the card must render, derived from
# the read-only mirror at ~/rmems/hf/grok-4.6/sparse-reward-long-tasks.
SPARSE_ITEM = {
    "slug": "sparse-reward-long-task-factory",
    "hub": SPARSE_REWARD,
    "pretty": "Sparse Reward Long Tasks",
    "blurb": "Sparse-reward leftover-goal long tasks (final reward only).",
    "tags": ["synthetic-data", "sparse-reward", "long-horizon"],
}
SPARSE_SUMMARY = dict(
    records=6551,
    bytes_=67907183,
    first="r01",
    last="r6551",
    names=["batch-r01.jsonl", "batch-r6551.jsonl"],
)


class SparseRewardLongTasksDeclarationTests(unittest.TestCase):
    """Issue #45: the union `reward` key-bag that broke the viewer's first cast.

    Every count asserted here was derived from the read-only mirror at
    ``~/rmems/hf/grok-4.6/sparse-reward-long-tasks`` (6551 records over 6551
    ``data/raw/batch-r*.jsonl`` shards, 0 parse failures), not from the issue
    text.
    """

    def setUp(self):
        self.declaration = card_schema.load(SPARSE_REWARD)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #45")
        self.item = dict(SPARSE_ITEM)
        self.card = publisher.render_card(
            self.item, summary=publisher.PayloadSummary(**SPARSE_SUMMARY)
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            [feature["name"] for feature in self.declaration["features"]],
            ["id", "goal", "plan", "steps", "outcome", "reward", "meta"],
        )
        # Unlike long-horizon-coding, every record here carries a `plan`.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("16252 of 211140 steps", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [45])

    def test_the_reward_key_bag_that_broke_the_cast_is_declared_json(self):
        # The viewer inferred struct<success: bool> from the early shards and
        # then could not cast terminal_only / horizon_steps. Both keys must be
        # named on the card, and `reward` must not be a struct.
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )
        reward_note = {
            feature["name"]: feature for feature in self.declaration["features"]
        }["reward"]["note"]
        for key in ("success", "terminal_only", "horizon_steps", "mid_reward_steps"):
            self.assertIn(f"`{key}`", reward_note)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        # No card-only annotation may leak into the YAML block.
        self.assertNotIn("optional:", front_matter)
        self.assertNotIn("note:", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_six_designed_leftover_mill_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        for record_id in (
            "srl-r6134-networkd-dhcp-ipv4-only-c67a",
            "srl-r6135-chrony-maxslewrate-vs-ntpd-ffb5",
            "srl-r6136-nft-flowtable-timeout-vs-ipt-035c",
            "srl-r6137-podman-events-logger-journald-e10f",
            "srl-r6138-buildah-format-oci-vs-docker-b703",
            "srl-r6139-skopeo-dest-tls-verify-db0f",
        ):
            self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)

    def test_card_body_owns_this_factory_as_the_source_of_the_frozen_census(self):
        # #43 froze the published factory_mix census: the srl-* rows it names
        # live in other dumps, so this card discloses the direction.
        self.assertIn("srl-r500-networkd-dhcp-ipv4-only-c67a", self.card)
        self.assertIn("observability-debug-trajectories", self.card)
        self.assertIn("eval-harness-trajectories", self.card)
        self.assertIn("/43", self.card)


if __name__ == "__main__":
    unittest.main()
