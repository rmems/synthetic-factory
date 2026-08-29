#!/usr/bin/env python3
"""Issue #70 leaf tests for the per-dataset card schema declaration."""

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


QUEUE_BACKPRESSURE = "queue-backpressure-trajectories"

QUEUE_BACKPRESSURE_MIRROR = (
    Path.home()
    / "rmems"
    / "hf"
    / "grok-4.6"
    / QUEUE_BACKPRESSURE
    / "data"
    / "raw"
)

# The published dump is batch-r01..batch-r141 with no gaps and no suffixed
# shards. The coverage cross-check inside render_card is fed this full list so
# an uncovered shard fails, rather than three hand-picked names that cannot.
SHARD_NAMES = [f"batch-r{number:02d}.jsonl" for number in range(1, 142)]


class QueueBackpressureDeclarationTests(unittest.TestCase):
    """Issue #70: thin `meta` vs designed/lane leftover schema.

    Counts asserted here were derived read-only from the published mirror
    ``~/rmems/hf/grok-4.6/queue-backpressure-trajectories``: 141 shards
    ``batch-r01``-``batch-r141``, 282 records, 0 parse failures, 4649 steps.
    """

    def setUp(self):
        self.declaration = card_schema.load(QUEUE_BACKPRESSURE)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #70")
        self.item = {
            "slug": "queue-backpressure-factory",
            "hub": QUEUE_BACKPRESSURE,
            "pretty": "Queue Backpressure Trajectories",
            "blurb": "Queue leftover-bound / backpressure episodes.",
            "tags": ["synthetic-data", "queues", "backpressure"],
        }
        self.card = publisher.render_card(
            self.item,
            records=282,
            bytes_=2048818,
            first="r01",
            last="r141",
            payload_names=list(SHARD_NAMES),
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # `plan` is a string on all 282 records here, unlike #36 where it is
        # optional: declaring it optional would understate the payload.
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("4448 of 4649", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [70])

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
        self.assertIn("  - name: plan\n    dtype: string\n", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_thin_meta_and_lane_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("`qbp-r01-amqp-prefetch-unbounded`", self.card)
        self.assertIn("`qbp-r09-huey-immediate-false-7b22`", self.card)
        self.assertIn("`qbp-r2-sqs-inflight-p3`", self.card)
        self.assertIn("`qbp-r3-rabbit-prefetch-p13`", self.card)
        self.assertIn("define the shape datasets-server inferred", self.card)
        self.assertIn("later designed records", self.declaration["note"])
        self.assertNotIn("every later shard", self.declaration["note"])
        self.assertIn("cast fails on the later 268 designed records", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)

    def test_card_body_owns_the_six_dest_stamped_sir_records(self):
        for record_id in (
            "sir-r74-bleve-alias-leftover3c-rebuild",
            "sir-r74-bleve-drop-leftover3c-handoff",
            "sir-r75-lucene-nrt-leftover3c-rebuild",
            "sir-r75-lucene-drop-leftover3c-handoff",
            "sir-r76-pg-trgm-conc-leftover3c-rebuild",
            "sir-r76-pg-trgm-drop-leftover3c-handoff",
        ):
            self.assertIn(f"`{record_id}`", self.card)
        # The class is disclosed as unowned, not as already tracked: rendering
        # it under a "Tracked in #43, #44" link would be an overclaim.
        self.assertIn("No GitHub issue currently owns this class", self.card)
        sir_disclosure = next(
            item
            for item in self.declaration["disclosures"]
            if any(record_id.startswith("sir-") for record_id in item["ids"])
        )
        self.assertEqual(sir_disclosure["issues"], [])
        self.assertEqual(len(sir_disclosure["ids"]), 6)

    def test_same_factory_leftover_naming_is_not_claimed_as_foreign_payload(self):
        self.assertIn("advertised leftover-bound mechanic", self.card)
        self.assertIn("96 name `leftover` in the id", self.card)
        self.assertIn("public `decision_basis` (4649 of 4649)", self.card)


    def test_every_published_shard_is_covered_by_the_declared_glob(self):
        """Feed all 141 shard names to the coverage check, not three samples."""
        self.assertEqual(len(SHARD_NAMES), 141)
        self.assertEqual(SHARD_NAMES[0], "batch-r01.jsonl")
        self.assertEqual(SHARD_NAMES[-1], "batch-r141.jsonl")
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, SHARD_NAMES), []
        )
        # An appended shard the glob cannot reach must be reported, so this
        # check can actually fail rather than merely being present.
        self.assertTrue(
            card_schema.payload_coverage_errors(
                {**self.declaration, "data_files": ["data/raw/batch-r0*.jsonl"]},
                SHARD_NAMES,
            )
        )

    @unittest.skipUnless(
        QUEUE_BACKPRESSURE_MIRROR.is_dir(),
        "read-only published mirror is not available",
    )
    def test_declaration_counts_match_the_published_mirror(self):
        """Re-derive the docstring's counts from the payload, not from the JSON.

        Every other assertion in this class compares the declaration against
        constants typed beside it, so none can fail when the declaration drifts
        from what was actually published. This one rescans the mirror.
        """
        shards = sorted(QUEUE_BACKPRESSURE_MIRROR.glob("batch-*.jsonl"))
        records = []
        for shard in shards:
            with shard.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        records.append((shard.name, json.loads(line)))
        self.assertEqual(len(shards), 141)
        self.assertEqual(len(records), 282)
        total = len(records)

        # The real published layout, not a fabricated name list. Compared as a
        # set because glob order is lexicographic (`batch-r100` sorts before
        # `batch-r11`) while the run is numbered numerically; equal sets of
        # equal length prove no gap, no extra and no suffixed shard.
        published = [shard.name for shard in shards]
        self.assertEqual(len(published), len(SHARD_NAMES))
        self.assertEqual(set(published), set(SHARD_NAMES))
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, published), []
        )

        names = {feature["name"]: feature for feature in self.declaration["features"]}
        optional = {n for n, f in names.items() if f.get("optional")}
        for shard, record in records:
            self.assertEqual(set(record) - set(names), set(), shard)
            self.assertEqual(set(names) - set(record) - optional, set(), shard)
            self.assertIsInstance(record["plan"], str)
        self.assertIn(f"present on all {total} records", names["plan"]["note"])

        step_names = {feature["name"]: feature for feature in names["steps"]["list"]}
        step_optional = {n for n, f in step_names.items() if f.get("optional")}
        total_steps = reflections = bases = 0
        for shard, record in records:
            for step in record["steps"]:
                total_steps += 1
                self.assertEqual(set(step) - set(step_names), set(), shard)
                self.assertEqual(
                    set(step_names) - set(step) - step_optional, set(), shard
                )
                self.assertEqual(set(step["tool_call"]), {"name", "args"})
                reflections += "reflection" in step
                bases += bool(step["decision_basis"])
        self.assertIn(
            f"present on {reflections} of {total_steps} steps",
            step_names["reflection"]["note"],
        )
        self.assertEqual(bases, total_steps)
        self.assertIn(f"`decision_basis` ({bases} of {total_steps})", self.card)

        bags = {}
        for bag in ("reward", "meta"):
            seen = {}
            for _shard, record in records:
                for key in record[bag]:
                    seen[key] = seen.get(key, 0) + 1
            bags[bag] = seen
        reward_note = names["reward"]["note"]
        self.assertEqual(
            {k for k, v in bags["reward"].items() if v == total},
            {"success", "tests_passed", "cost_steps"},
        )
        self.assertIn(f"`plan_changes` on {bags['reward']['plan_changes']}", reward_note)
        self.assertIn(f"`retries` on {bags['reward']['retries']}", reward_note)
        self.assertIn(
            f"`wasted_calls` on {bags['reward']['wasted_calls']}", reward_note
        )
        self.assertIn(f"`xfailed` on {bags['reward']['xfailed']}", reward_note)

        designed = bags["meta"]["kind"]
        lane_count = bags["meta"]["lane"]
        meta_note = names["meta"]["note"]
        self.assertEqual(
            {k for k, v in bags["meta"].items() if v == total},
            {"factory", "generator", "round"},
        )
        self.assertIn(f"{designed} add `kind`", meta_note)
        self.assertIn(f"{lane_count} of those also add `lane`", meta_note)
        self.assertIn(f"{total - designed} carry the thin", meta_note)
        self.assertIn(f"cast fails on the later {designed} designed records", self.card)

        # Each disclosed id list must be exactly the set the payload produces.
        disclosed = {}
        for item in self.declaration["disclosures"]:
            if isinstance(item, dict):
                disclosed[frozenset(item["ids"])] = item
        thin = {r["id"] for _s, r in records if "kind" not in r["meta"]}
        lane = {r["id"] for _s, r in records if "lane" in r["meta"]}
        sir = {r["id"] for _s, r in records if r["id"].startswith("sir-")}
        for derived in (thin, lane, sir):
            self.assertIn(frozenset(derived), disclosed, sorted(derived))
        self.assertEqual(len(thin), total - designed)
        self.assertEqual(len(lane), lane_count)
        self.assertEqual(len(sir), 6)
        # The 4 `lane` records are the same 4 whose reward omits `plan_changes`.
        self.assertEqual(
            lane, {r["id"] for _s, r in records if "plan_changes" not in r["reward"]}
        )
        # The dest-stamped foreign rows really are invisible to both detectors.
        foreign = [r for _s, r in records if r["id"] in sir]
        self.assertEqual({r["meta"]["factory"] for r in foreign}, {QUEUE_BACKPRESSURE.replace("-trajectories", "-factory")})
        self.assertEqual({r["meta"]["kind"] for r in foreign}, {"episode"})
        self.assertEqual(
            sum(
                1
                for r in foreign
                if "handoff" in r["reward"] or "xfailed" in r["reward"]
            ),
            3,
        )

        # The same-factory leftover naming counts the card prints.
        own = [r for _s, r in records if r["id"].startswith("qbp-")]
        self.assertEqual(len(own), total - len(sir))
        self.assertIn(
            f"{sum(1 for r in own if 'leftover' in r['id'])} name `leftover` in the id",
            self.card,
        )
        self.assertIn(
            f"{sum(1 for r in own if 'leftover' in r['goal'])} name it in the goal",
            self.card,
        )


if __name__ == "__main__":
    unittest.main()
