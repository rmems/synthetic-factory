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

_SCAN: dict = {}

_needs_mirror = unittest.skipUnless(
    INFRA_AS_CODE_MIRROR.is_dir(),
    "read-only published mirror is not available",
)


def _scan_mirror():
    """Read every published shard once and memoize it for the whole module."""
    if "scan" in _SCAN:
        return _SCAN["scan"]
    payloads = sorted(INFRA_AS_CODE_MIRROR.glob("batch-*.jsonl"))
    per_shard = []
    for payload in payloads:
        with payload.open(encoding="utf-8") as handle:
            per_shard.append(
                (payload.name, [json.loads(line) for line in handle if line.strip()])
            )
    records = [record for _name, rows in per_shard for record in rows]
    _SCAN["scan"] = (per_shard, records)
    return _SCAN["scan"]


def _reward_census(records):
    """Per-key record counts plus the value type census of `reward.handoff`."""
    reward_counts: dict = {}
    handoff_types: dict = {}
    for record in records:
        for key, value in record["reward"].items():
            reward_counts[key] = reward_counts.get(key, 0) + 1
            if key == "handoff":
                kind = type(value).__name__
                handoff_types[kind] = handoff_types.get(kind, 0) + 1
    return reward_counts, handoff_types


def _reflection_rounds(records):
    """The `meta.round` of every step that carries a `reflection`."""
    return [
        record["meta"]["round"]
        for record in records
        for step in record["steps"]
        if "reflection" in step
    ]


def _meta_split(records):
    """The thin-`meta` record count and the sorted rounds of the wide records."""
    thin = sum(
        1
        for record in records
        if set(record["meta"]) == {"factory", "generator", "round"}
    )
    wide_rounds = sorted(
        record["meta"]["round"] for record in records if "kind" in record["meta"]
    )
    return thin, wide_rounds


def _feature(declaration, name):
    """The top-level feature declaration called ``name``."""
    return next(f for f in declaration["features"] if f["name"] == name)


def _step_feature(declaration, name):
    """The step-list feature declaration called ``name``."""
    return next(
        f for f in _feature(declaration, "steps")["list"] if f["name"] == name
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
        meta = _feature(self.declaration, "meta")
        # 4190 thin + 1018 wide = 5208 records; the wide rounds are contiguous.
        for fragment in ("1018", "78-586", "4190", "1-77", "587-2604", "sim_or_real"):
            self.assertIn(fragment, meta["note"])

    def test_reward_note_names_the_only_type_varying_key(self):
        reward = _feature(self.declaration, "reward")
        # `handoff` is the single int-or-string key; the tests_* counters are not.
        self.assertIn("`handoff` is the only key whose value type varies", reward["note"])
        for singleton in ("wrong_cluster_apply", "replicas", "targets_healthy"):
            self.assertIn(singleton, reward["note"])

    # -- Re-derived from the payload, not from the declaration -------------
    #
    # Rounds 1417-2604 were published on 2026-08-26, after the issue #67
    # census was derived at the r1416 frontier. The three mirror-backed tests
    # below re-derive the declared totals from the payload, so a declaration
    # still carrying the r1416-frontier counts fails, and they pin the claim
    # that the growth widened nothing: no new reward key, no new tool, no new
    # arg key, and no `reflection` outside rounds 1-1416.

    @_needs_mirror
    def test_published_mirror_layout_matches_the_r2604_release(self):
        per_shard, records = _scan_mirror()
        self.assertEqual(len(per_shard), 2604)
        self.assertEqual({len(rows) for _name, rows in per_shard}, {2})
        self.assertEqual(len(records), 5208)
        self.assertEqual(len({record["id"] for record in records}), 5208)

    @_needs_mirror
    def test_published_mirror_reconciles_the_reflection_and_meta_growth(self):
        _per_shard, records = _scan_mirror()
        steps_total = sum(len(record["steps"]) for record in records)
        reflections = _reflection_rounds(records)
        thin, wide_rounds = _meta_split(records)
        self.assertEqual(steps_total, 87554)
        self.assertEqual(len(reflections), 17436)
        self.assertLessEqual(max(reflections), 1416)
        self.assertEqual(thin, 4190)
        self.assertEqual(len(wide_rounds), 1018)
        self.assertEqual((wide_rounds[0], wide_rounds[-1]), (78, 586))
        self.assertIn(
            f"on all {len(records)} records",
            _feature(self.declaration, "meta")["note"],
        )
        self.assertIn(
            f"{len(reflections)} of {steps_total}",
            _step_feature(self.declaration, "reflection")["note"],
        )

    @_needs_mirror
    def test_published_mirror_reconciles_the_reward_census(self):
        _per_shard, records = _scan_mirror()
        reward_counts, handoff_types = _reward_census(records)
        self.assertEqual(reward_counts["tests_passed"], 5180)
        self.assertEqual(reward_counts["handoff"], 2606)
        self.assertEqual(reward_counts["tests_failed"], 2576)
        self.assertEqual(handoff_types, {"int": 2593, "str": 13})
        self.assertIn(
            f"`handoff` on {reward_counts['handoff']}",
            _feature(self.declaration, "reward")["note"],
        )

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
