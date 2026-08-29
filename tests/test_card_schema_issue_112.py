#!/usr/bin/env python3
"""Issue #52 leaf tests for the per-dataset card schema declaration."""

import re

import test_card_schema_integration as _shared

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


WEBSOCKET_RECONNECT = "websocket-reconnect-trajectories"

WEBSOCKET_RECONNECT_MIRROR = (
    Path.home()
    / "rmems"
    / "hf"
    / "grok-4.6"
    / WEBSOCKET_RECONNECT
    / "data"
    / "raw"
)


_SCAN: dict = {}


def _scan_mirror():
    """Re-derive the declaration's payload facts from the published shards.

    Memoized: several tests below re-derive different facts from one scan.
    """
    if "scan" in _SCAN:
        return _SCAN["scan"]
    shards = sorted(WEBSOCKET_RECONNECT_MIRROR.glob("batch-*.jsonl"))
    records = []
    for shard in shards:
        with shard.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append((shard.name, json.loads(line)))
    _SCAN["scan"] = (shards, records)
    return _SCAN["scan"]


_needs_mirror = unittest.skipUnless(
    WEBSOCKET_RECONNECT_MIRROR.is_dir(),
    "read-only published mirror is not available",
)


def _feature_index(features):
    """Split a feature list into a name lookup and the set of optional names."""
    names = {feature["name"]: feature for feature in features}
    return names, {n for n, f in names.items() if f.get("optional")}


def _iter_steps(records):
    """Yield every (shard, step) pair, flattening the record/step nesting."""
    for shard, record in records:
        for step in record["steps"]:
            yield shard, step


def _bag_key_counts(records, bag):
    """Count how many records carry each key of a free-form bag."""
    seen = {}
    for _shard, record in records:
        for key in record[bag]:
            seen[key] = seen.get(key, 0) + 1
    return seen


class WebsocketReconnectDeclarationTests(unittest.TestCase):
    """Issue #52: thin `meta` in batch-r01 vs `designed`/`domain`/`stack` later."""

    def setUp(self):
        self.declaration = card_schema.load(WEBSOCKET_RECONNECT)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #52")
        self.item = {
            "slug": "websocket-reconnect-factory",
            "hub": WEBSOCKET_RECONNECT,
            "pretty": "Websocket Reconnect Trajectories",
            "blurb": "WebSocket leftover-resume / reconnect episodes.",
            "tags": ["synthetic-data", "trajectories", "websocket"],
        }
        self.card = publisher.render_card(
            self.item,
            records=322,
            bytes_=2375680,
            first="r01",
            last="r161",
            payload_names=["batch-r01.jsonl", "batch-r161.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # Unlike #36's dataset, every one of the 322 records carries a `plan`.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("5081 of 5314 steps", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [52])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_meta_note_records_the_thin_and_lane_subsets(self):
        meta = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "meta"
        )
        for key in ("kind", "seed", "designed", "domain", "stack"):
            self.assertIn(f"`{key}`", meta["note"])
        self.assertIn("312 of 322", meta["note"])
        self.assertIn("`lane` on 12 of 322", meta["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_ten_thin_meta_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertIn("`wsr-r01-resubscribe-on-reconnect`", self.card)
        self.assertIn("`wsr-r11-close-1005-backoff-7c2d`", self.card)
        self.assertIn("`meta.lane`", self.card)
        self.assertIn("no dest-stamped foreign payload", self.card)
        self.assertIn("does not infer generator-file provenance", self.card)
        self.assertNotIn("mill_wsr_leftover", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)


    def test_card_payload_prose_names_real_batch_shards(self):
        """Every `data/raw/batch-*.jsonl` the card prints must be a real shard.

        Regression guard for a fixture that passed `first="01"` / `last="161"`
        and so advertised `data/raw/batch-01.jsonl` -- a filename the publisher
        can never emit. `batch_label` derives labels as `r{number:02d}`, and
        `snapshot_one` only fills `first`/`last` when every shard is named
        `batch-{label}.jsonl`, so the rendered range is always `batch-rNN`.
        """
        printed = set(re.findall(r"data/raw/(batch-[0-9a-z]+\.jsonl)", self.card))
        self.assertIn("batch-r01.jsonl", printed)
        self.assertIn("batch-r161.jsonl", printed)
        for name in printed:
            with self.subTest(name=name):
                self.assertIsNotNone(
                    publisher.BATCH_NAME_RE.fullmatch(name),
                    f"{name} is not a shard name the publisher can produce",
                )
                label = publisher.batch_label(Path(name))
                self.assertEqual(f"batch-{label[2]}.jsonl", name)

    # -- Re-derived from the payload, not from the declaration -------------
    #
    # The other tests in this class compare the declaration against constants
    # typed alongside it, so they cannot catch the failure this declaration
    # exists to prevent: drifting away from what was actually published. The
    # tests below scan the read-only mirror and assert the declaration still
    # describes it.

    @_needs_mirror
    def test_published_shard_and_record_counts_match_the_declaration(self):
        shards, records = _scan_mirror()
        self.assertEqual(len(shards), 161)
        self.assertEqual(len(records), 322)

    @_needs_mirror
    def test_every_record_carries_exactly_the_declared_top_level_fields(self):
        _shards, records = _scan_mirror()
        names, optional = _feature_index(self.declaration["features"])
        for shard, record in records:
            self.assertEqual(set(record) - set(names), set(), shard)
            self.assertEqual(set(names) - set(record) - optional, set(), shard)
            self.assertIsInstance(record["plan"], str)
            self.assertTrue(record["plan"].strip(), record["id"])
        self.assertIn(f"all {len(records)} records", names["plan"]["note"])

    @_needs_mirror
    def test_every_step_carries_exactly_the_declared_step_fields(self):
        _shards, records = _scan_mirror()
        names, _optional = _feature_index(self.declaration["features"])
        step_names, step_optional = _feature_index(names["steps"]["list"])
        for shard, step in _iter_steps(records):
            self.assertEqual(set(step) - set(step_names), set(), shard)
            self.assertEqual(set(step_names) - set(step) - step_optional, set(), shard)
            self.assertEqual(set(step["tool_call"]), {"name", "args"})

    @_needs_mirror
    def test_step_note_matches_the_published_reflection_count(self):
        _shards, records = _scan_mirror()
        names, _optional = _feature_index(self.declaration["features"])
        step_names, _step_optional = _feature_index(names["steps"]["list"])
        steps = [step for _shard, step in _iter_steps(records)]
        reflections = sum(1 for step in steps if "reflection" in step)
        self.assertIn(
            f"present on {reflections} of {len(steps)} steps",
            step_names["reflection"]["note"],
        )

    @_needs_mirror
    def test_both_key_bags_are_dicts_with_the_declared_always_present_keys(self):
        _shards, records = _scan_mirror()
        total = len(records)
        for bag in ("reward", "meta"):
            for _shard, record in records:
                self.assertIsInstance(record[bag], dict)
        self.assertEqual(
            {k for k, v in _bag_key_counts(records, "meta").items() if v == total},
            {"factory", "generator", "round"},
        )
        self.assertEqual(
            {k for k, v in _bag_key_counts(records, "reward").items() if v == total},
            {"success", "tests_passed", "cost_steps"},
        )

    @_needs_mirror
    def test_meta_note_matches_the_published_key_counts(self):
        _shards, records = _scan_mirror()
        names, _optional = _feature_index(self.declaration["features"])
        counts = _bag_key_counts(records, "meta")
        total = len(records)
        meta_note = names["meta"]["note"]
        self.assertIn(f"`stack` on {counts['kind']} of {total}", meta_note)
        self.assertIn(f"`lane` on {counts['lane']} of {total}", meta_note)

    @_needs_mirror
    def test_reward_note_matches_the_published_key_counts(self):
        _shards, records = _scan_mirror()
        names, _optional = _feature_index(self.declaration["features"])
        counts = _bag_key_counts(records, "reward")
        total = len(records)
        reward_note = names["reward"]["note"]
        self.assertIn(f"`wasted_calls` on {counts['retries']} of {total}", reward_note)
        self.assertIn(
            f"`plan_changes` on {counts['plan_changes']} of {total}", reward_note
        )
        self.assertIn(f"`handoff` on {counts['handoff']}", reward_note)
        self.assertIn(f"`xfailed` on {counts['xfailed']}", reward_note)

    @_needs_mirror
    def test_disclosed_thin_meta_ids_are_exactly_the_records_without_kind(self):
        _shards, records = _scan_mirror()
        thin = {
            record["id"] for _shard, record in records if "kind" not in record["meta"]
        }
        declared = {
            record_id
            for item in self.declaration["disclosures"]
            if isinstance(item, dict)
            for record_id in item["ids"]
        }
        self.assertEqual(declared, thin)

    @_needs_mirror
    def test_two_thin_meta_records_sit_in_the_batch_the_cast_is_built_on(self):
        _shards, records = _scan_mirror()
        self.assertEqual(
            sum(
                1
                for shard, record in records
                if shard == "batch-r01.jsonl" and "kind" not in record["meta"]
            ),
            2,
        )

    @_needs_mirror
    def test_record_ids_are_unique_and_namespaced_to_this_factory(self):
        _shards, records = _scan_mirror()
        ids = [record["id"] for _shard, record in records]
        self.assertEqual(len(set(ids)), len(ids))
        self.assertTrue(all(record_id.startswith("wsr-") for record_id in ids))


if __name__ == "__main__":
    unittest.main()
