#!/usr/bin/env python3
"""Issue #70 leaf tests for the per-dataset card schema declaration."""

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


_needs_mirror = unittest.skipUnless(
    QUEUE_BACKPRESSURE_MIRROR.is_dir(),
    "read-only published mirror is not available",
)


def _load_mirror_records(mirror):
    """Read every payload record in the mirror, tagged with its shard name."""
    shards = sorted(mirror.glob("batch-*.jsonl"))
    records = []
    for shard in shards:
        with shard.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append((shard.name, json.loads(line)))
    return shards, records


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


def _ids_where(records, predicate):
    """The set of record ids whose record matches a predicate."""
    return {record["id"] for _shard, record in records if predicate(record)}


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

    # -- Re-derived from the payload, not from the declaration -------------
    #
    # Every assertion above compares the declaration against constants typed
    # beside it, so none can fail when the declaration drifts from what was
    # actually published. The tests below rescan the published mirror instead.

    @classmethod
    def _mirror(cls):
        """Scan the published mirror once, then reuse it across these tests."""
        if getattr(cls, "_mirror_cache", None) is None:
            cls._mirror_cache = _load_mirror_records(QUEUE_BACKPRESSURE_MIRROR)
        return cls._mirror_cache

    @_needs_mirror
    def test_published_shards_are_exactly_the_declared_shard_list(self):
        """The real published layout, not a fabricated name list.

        Compared as a set because glob order is lexicographic (`batch-r100`
        sorts before `batch-r11`) while the run is numbered numerically; equal
        sets of equal length prove no gap, no extra and no suffixed shard.
        """
        shards, records = self._mirror()
        self.assertEqual(len(shards), 141)
        self.assertEqual(len(records), 282)
        published = [shard.name for shard in shards]
        self.assertEqual(len(published), len(SHARD_NAMES))
        self.assertEqual(set(published), set(SHARD_NAMES))
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, published), []
        )

    @_needs_mirror
    def test_every_record_carries_exactly_the_declared_top_level_fields(self):
        _shards, records = self._mirror()
        names, optional = _feature_index(self.declaration["features"])
        for shard, record in records:
            self.assertEqual(set(record) - set(names), set(), shard)
            self.assertEqual(set(names) - set(record) - optional, set(), shard)
            self.assertIsInstance(record["plan"], str)
        self.assertIn(f"present on all {len(records)} records", names["plan"]["note"])

    @_needs_mirror
    def test_every_step_carries_exactly_the_declared_step_fields(self):
        _shards, records = self._mirror()
        names, _optional = _feature_index(self.declaration["features"])
        step_names, step_optional = _feature_index(names["steps"]["list"])
        for shard, step in _iter_steps(records):
            self.assertEqual(set(step) - set(step_names), set(), shard)
            self.assertEqual(set(step_names) - set(step) - step_optional, set(), shard)
            self.assertEqual(set(step["tool_call"]), {"name", "args"})

    @_needs_mirror
    def test_step_notes_match_the_reflection_and_decision_basis_counts(self):
        _shards, records = self._mirror()
        names, _optional = _feature_index(self.declaration["features"])
        step_names, _step_optional = _feature_index(names["steps"]["list"])
        steps = [step for _shard, step in _iter_steps(records)]
        total_steps = len(steps)
        reflections = sum(1 for step in steps if "reflection" in step)
        bases = sum(1 for step in steps if step["decision_basis"])
        self.assertIn(
            f"present on {reflections} of {total_steps} steps",
            step_names["reflection"]["note"],
        )
        self.assertEqual(bases, total_steps)
        self.assertIn(f"`decision_basis` ({bases} of {total_steps})", self.card)

    @_needs_mirror
    def test_reward_note_matches_the_published_reward_key_counts(self):
        _shards, records = self._mirror()
        names, _optional = _feature_index(self.declaration["features"])
        counts = _bag_key_counts(records, "reward")
        note = names["reward"]["note"]
        self.assertEqual(
            {k for k, v in counts.items() if v == len(records)},
            {"success", "tests_passed", "cost_steps"},
        )
        self.assertIn(f"`plan_changes` on {counts['plan_changes']}", note)
        self.assertIn(f"`retries` on {counts['retries']}", note)
        self.assertIn(f"`wasted_calls` on {counts['wasted_calls']}", note)
        self.assertIn(f"`xfailed` on {counts['xfailed']}", note)

    @_needs_mirror
    def test_meta_note_matches_the_designed_and_lane_record_counts(self):
        _shards, records = self._mirror()
        names, _optional = _feature_index(self.declaration["features"])
        total = len(records)
        counts = _bag_key_counts(records, "meta")
        designed = counts["kind"]
        note = names["meta"]["note"]
        self.assertEqual(
            {k for k, v in counts.items() if v == total},
            {"factory", "generator", "round"},
        )
        self.assertIn(f"{designed} add `kind`", note)
        self.assertIn(f"{counts['lane']} of those also add `lane`", note)
        self.assertIn(f"{total - designed} carry the thin", note)
        self.assertIn(f"cast fails on the later {designed} designed records", self.card)

    @_needs_mirror
    def test_each_disclosed_id_list_is_exactly_what_the_payload_produces(self):
        _shards, records = self._mirror()
        counts = _bag_key_counts(records, "meta")
        disclosed = {
            frozenset(item["ids"])
            for item in self.declaration["disclosures"]
            if isinstance(item, dict)
        }
        thin = _ids_where(records, lambda r: "kind" not in r["meta"])
        lane = _ids_where(records, lambda r: "lane" in r["meta"])
        sir = _ids_where(records, lambda r: r["id"].startswith("sir-"))
        for derived in (thin, lane, sir):
            self.assertIn(frozenset(derived), disclosed, sorted(derived))
        self.assertEqual(len(thin), len(records) - counts["kind"])
        self.assertEqual(len(lane), counts["lane"])
        self.assertEqual(len(sir), 6)
        # The 4 `lane` records are the same 4 whose reward omits `plan_changes`.
        self.assertEqual(
            lane, _ids_where(records, lambda r: "plan_changes" not in r["reward"])
        )

    @_needs_mirror
    def test_dest_stamped_foreign_rows_are_invisible_to_both_detectors(self):
        _shards, records = self._mirror()
        foreign = [r for _shard, r in records if r["id"].startswith("sir-")]
        self.assertEqual(
            {r["meta"]["factory"] for r in foreign},
            {QUEUE_BACKPRESSURE.replace("-trajectories", "-factory")},
        )
        self.assertEqual({r["meta"]["kind"] for r in foreign}, {"episode"})
        self.assertEqual(
            sum(
                1
                for r in foreign
                if "handoff" in r["reward"] or "xfailed" in r["reward"]
            ),
            3,
        )

    @_needs_mirror
    def test_same_factory_leftover_naming_counts_match_the_card(self):
        _shards, records = self._mirror()
        sir = _ids_where(records, lambda r: r["id"].startswith("sir-"))
        own = [r for _shard, r in records if r["id"].startswith("qbp-")]
        self.assertEqual(len(own), len(records) - len(sir))
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
